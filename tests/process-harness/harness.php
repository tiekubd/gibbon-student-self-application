<?php
/**
 * Phase 1 test harness: runs the changed form-builder processes against Gibbon v30.0.01's
 * own classes, with the mailer, session, payment and email template stubbed out.
 * Usage: php harness.php <dir with changed files: orig|new>
 */
declare(strict_types=0);

$variant = $argv[1] ?? 'new';
$overrideRoot = __DIR__ . '/' . $variant;
$coreRoot = getenv('GIBBON_ROOT') ?: '/tmp/g30'; // unpacked Gibbon v30.0.01 source

// ---------------------------------------------------------------------------
// Minimal globals and framework stand-ins (no vendor/ available)
// ---------------------------------------------------------------------------
function __($s, $p = []) { foreach ($p as $k => $v) $s = str_replace('{'.$k.'}', $v, $s); return $s; }

eval('namespace Gibbon\Http; class Url {
    private $s; public function __construct($s = "") { $this->s = $s; }
    public static function fromModuleRoute($m, $r) { return new self("/$m/$r"); }
    public function withQueryParams(array $p) { return new self($this->s."?".http_build_query($p)); }
    public function withAbsoluteUrl() { return new self("https://test".$this->s); }
    public function __toString() { return $this->s; }
}');

eval('namespace League\Container; interface ContainerAwareInterface {} trait ContainerAwareTrait { protected $container; }');
eval('namespace League\Container\Exception; class NotFoundException extends \Exception {}');

spl_autoload_register(function ($class) use ($overrideRoot, $coreRoot) {
    if (strpos($class, 'Gibbon\\') !== 0) return;
    $rel = 'src/' . str_replace('\\', '/', substr($class, 7)) . '.php';
    foreach ([$overrideRoot . '/' . $rel, $coreRoot . '/' . $rel] as $file) {
        if (is_file($file)) { require $file; return; }
    }
});

/** Generate a stub implementing an interface; every method returns a type-safe empty value
 *  unless overridden in $fn, and any undeclared call is recorded via __call. */
function stub(string $interface, array $fn = []) {
    static $n = 0; $n++;
    $cls = 'Stub' . $n;
    $methods = '';
    foreach ((new ReflectionClass($interface))->getMethods() as $m) {
        $params = [];
        foreach ($m->getParameters() as $p) {
            $s = ($p->hasType() ? $p->getType() . ' ' : '') . ($p->isPassedByReference() ? '&' : '') . ($p->isVariadic() ? '...' : '') . '$' . $p->getName();
            if ($p->isDefaultValueAvailable()) $s .= ' = ' . var_export($p->getDefaultValue(), true);
            $params[] = $s;
        }
        $rt = $m->hasReturnType() ? (string) $m->getReturnType() : '';
        $default = ['bool' => 'false', 'string' => "''", 'array' => '[]', 'int' => '0', 'void' => ''][ltrim($rt, '?')] ?? 'null';
        $ret = $rt === 'void' ? '' : "return \$r ?? $default;";
        $methods .= "public function {$m->getName()}(" . implode(', ', $params) . ")" . ($rt ? ": $rt" : '') .
            " { \$r = \$this->call('{$m->getName()}', func_get_args()); $ret }\n";
    }
    eval("class $cls implements \\$interface { public \$fn = []; public \$calls = [];
        private function call(\$name, \$args) { \$this->calls[] = [\$name, \$args];
            \$k = strtolower(\$name); foreach (\$this->fn as \$f => \$c) if (strtolower(\$f) == \$k) return \$c(...\$args); return null; }
        public function __call(\$name, \$args) { return \$this->call(\$name, \$args); }
        $methods }");
    $o = new $cls; $o->fn = $fn; return $o;
}

class TestTemplate extends \Gibbon\Comms\EmailTemplate {
    public $data = [];
    public function __construct() {}
    public function setTemplateByID($id) { $this->data['templateID'] = $id; return $this; }
    public function renderSubject($data) { return 'Subject'; }
    public function renderBody($data) { $this->data = array_merge($this->data, $data); return 'Body'; }
}

class TestBuilder extends \Gibbon\Forms\Builder\FormBuilder {
    public function __construct(array $fieldNames, array $config, array $details = ['name' => 'Test Form']) {
        $this->fields = [];
        foreach ($fieldNames as $f) $this->fields[$f] = ['fieldName' => $f, 'fieldGroup' => 'StudentFields', 'fieldType' => 'varchar', 'label' => $f];
        $this->config = $config;
        $this->details = $details;
    }
    public function getFieldGroup($fieldGroup): \Gibbon\Forms\Builder\Fields\FieldGroupInterface {
        return stub(\Gibbon\Forms\Builder\Fields\FieldGroupInterface::class, [
            'displayFieldValue' => function ($b, $name, $field, &$data = []) { return $data[$name] ?? ''; },
        ]);
    }
}

class TestData extends \Gibbon\Forms\Builder\AbstractFormStorage {
    public function identify(string $identifier): int { return 1; }
    public function load(string $identifier): bool { return true; }
    public function save(string $identifier): bool { return true; }
}

function data(array $values, array $results = [], bool $readOnly = false) {
    $d = new TestData();
    $d->setData($values);
    foreach ($results as $k => $v) $d->setResult($k, $v);
    if ($readOnly) $d->setReadOnly(true);
    return $d;
}

function mailer() {
    return stub(\Gibbon\Contracts\Comms\Mailer::class, ['send' => fn () => true]);
}
function addresses($mail) {
    return array_map(fn ($c) => $c[1][0], array_values(array_filter($mail->calls, fn ($c) => strtolower($c[0]) == 'addaddress')));
}
$session = stub(\Gibbon\Contracts\Services\Session::class, ['get' => fn ($k, $d = null) => ['currency' => 'GHS ', 'organisationAdmissionsEmail' => 'admissions@school.test', 'organisationAdmissionsName' => 'Admissions'][$k] ?? $d]);

// Format::date needs date settings
$fmt = new ReflectionClass(\Gibbon\Services\Format::class);
if ($fmt->hasProperty('settings')) {
    $p = $fmt->getProperty('settings'); $p->setAccessible(true);
    $p->setValue(null, array_merge((array) $p->getValue(), ['dateFormatPHP' => 'd/m/Y', 'dateFormatIntlPHP' => 'dd/MM/yyyy', 'dateTimeFormatPHP' => 'd/m/Y H:i']));
}

// ---------------------------------------------------------------------------
// Fixtures: a student self-application and a parent application
// ---------------------------------------------------------------------------
$studentFields = ['surname', 'firstName', 'preferredName', 'officialName', 'email', 'homeAddress'];
$parentFields  = array_merge($studentFields, ['parent1title', 'parent1surname', 'parent1preferredName', 'parent1email', 'parent1relationship']);

$student = ['surname' => 'Mensah', 'firstName' => 'Ama', 'preferredName' => 'Ama', 'officialName' => 'Ama Mensah', 'email' => 'ama@student.test', 'homeAddress' => '1 Main St'];
$parent  = $student + ['parent1title' => 'Mrs.', 'parent1surname' => 'Mensah', 'parent1preferredName' => 'Efua', 'parent1email' => 'efua@parent.test', 'parent1relationship' => 'Mother'];

$results = [];
function check($label, $actual, $expected) {
    global $results;
    $ok = $actual === $expected;
    $results[] = $ok;
    printf("  [%s] %s\n", $ok ? 'PASS' : 'FAIL', $label);
    if (!$ok) printf("         expected: %s\n         actual:   %s\n", json_encode($expected), json_encode($actual));
}
function greeting(TestTemplate $t) {
    return trim(preg_replace('/\s+/', ' ', 'Dear ' . ($t->data['parentTitle'] ?? '') . ' ' . ($t->data['parentPreferredName'] ?? '') . ' ' . ($t->data['parentSurname'] ?? ''))) . ',';
}

use Gibbon\Forms\Builder\Process\SendSubmissionEmail;
use Gibbon\Forms\Builder\Process\PayProcessingFee;
use Gibbon\Forms\Builder\Process\SendAcceptanceEmail;
use Gibbon\Forms\Builder\Exception\MissingFieldException;

echo "=== Variant: $variant ===\n";

// --- SendSubmissionEmail ----------------------------------------------------
echo "\nSendSubmissionEmail\n";
$t = new TestTemplate; $m = mailer();
(new SendSubmissionEmail($session, $m, $t))->process(new TestBuilder($studentFields, ['accountEmail' => 'ama@student.test', 'submissionEmailTemplate' => '11']), data($student));
check('Student form: greeting uses the student', greeting($t), 'Dear Ama Mensah,');
check('Student form: sent once, to the account email', addresses($m), ['ama@student.test']);

$t = new TestTemplate; $m = mailer();
(new SendSubmissionEmail($session, $m, $t))->process(new TestBuilder($parentFields, ['accountEmail' => 'efua@work.test', 'submissionEmailTemplate' => '11']), data($parent));
check('Parent form: greeting still uses Parent 1', greeting($t), 'Dear Mrs. Efua Mensah,');
check('Parent form: account email + parent1email (an address, not true)', addresses($m), ['efua@work.test', 'efua@parent.test']);

$t = new TestTemplate; $m = mailer();
(new SendSubmissionEmail($session, $m, $t))->process(new TestBuilder($parentFields, ['accountEmail' => 'efua@parent.test', 'submissionEmailTemplate' => '11']), data($parent));
check('Parent form: no duplicate when parent1email = account email', addresses($m), ['efua@parent.test']);

// --- PayProcessingFee -------------------------------------------------------
echo "\nPayProcessingFee\n";
$payOn = stub(\Gibbon\Contracts\Services\Payment::class, ['isEnabled' => fn () => true]);
$payOff = stub(\Gibbon\Contracts\Services\Payment::class, ['isEnabled' => fn () => false]);
$cfg = ['formProcessingFee' => '50', 'formProcessingEmailTemplate' => '20', 'accountEmail' => 'ama@student.test'];

$verify = function ($pay, $fields) use ($session) {
    try { (new PayProcessingFee($session, $pay, mailer(), new TestTemplate))->verify(new TestBuilder($fields, [])); return 'ok'; }
    catch (MissingFieldException $e) { return 'missing: ' . $e->getMessage(); }
};
check('verify: student form + gateway is available', $verify($payOn, $studentFields), 'ok');
check('verify: parent form + gateway is available', $verify($payOn, $parentFields), 'ok');
check('verify: no gateway is still inactive', $verify($payOff, $studentFields), 'missing: Payment Gateway');
check('verify: form with no email field at all is inactive', $verify($payOn, ['surname', 'preferredName']), 'missing: parent1email,email');

// Form Builder's Inactive Features list: verify() first, then getRequiredFields() minus fields present
$inactiveList = function ($fields) use ($session, $payOff) {
    $process = new PayProcessingFee($session, $payOff, mailer(), new TestTemplate);
    $builder = new TestBuilder($fields, []);
    try { $process->verify($builder); } catch (MissingFieldException $e) {}
    return implode(', ', array_values(array_filter($process->getRequiredFields(), fn ($f) => !$builder->hasField($f))));
};
check('Inactive list, student form: only Payment Gateway', $inactiveList($studentFields), 'Payment Gateway');
check('Inactive list, parent form: only Payment Gateway', $inactiveList($parentFields), 'Payment Gateway');
check('Inactive list, no email field: names both options', $inactiveList(['surname']), 'Payment Gateway, parent1email, email');

$t = new TestTemplate; $m = mailer();
(new PayProcessingFee($session, $payOn, $m, $t))->process(new TestBuilder($studentFields, $cfg), data($student));
check('Student form: fee request goes to the student', addresses($m), ['ama@student.test']);
check('Student form: greeting uses the student', greeting($t), 'Dear Ama Mensah,');
check('Student form: template email variable = student', $t->data['email'] ?? null, 'ama@student.test');

$t = new TestTemplate; $m = mailer();
(new PayProcessingFee($session, $payOn, $m, $t))->process(new TestBuilder($parentFields, $cfg), data($parent));
check('Parent form: fee request still goes to Parent 1', addresses($m), ['efua@parent.test']);
check('Parent form: greeting still uses Parent 1', greeting($t), 'Dear Mrs. Efua Mensah,');

// --- SendAcceptanceEmail ----------------------------------------------------
echo "\nSendAcceptanceEmail\n";
$acc = fn ($tpl) => array_filter(['acceptanceEmailStudentTemplate' => '13', 'acceptanceEmailParentTemplate' => $tpl]);
$m = mailer();
(new SendAcceptanceEmail($session, $m, new TestTemplate))->process(new TestBuilder($parentFields, $acc('')), data($parent, ['informParents' => 'Y', 'parent1username' => 'emensah'], true));
check('Blank parent template: no parent email attempted', addresses($m), []);
$m = mailer();
(new SendAcceptanceEmail($session, $m, new TestTemplate))->process(new TestBuilder($parentFields, $acc('12')), data($parent, ['informParents' => 'Y', 'parent1username' => 'emensah'], true));
check('Parent template set: parent email still sent', addresses($m), ['efua@parent.test']);
$m = mailer();
(new SendAcceptanceEmail($session, $m, new TestTemplate))->process(new TestBuilder($studentFields, $acc('')), data($student, ['informStudent' => 'Y', 'username' => 'amensah'], true));
check('Student form: student welcome email still sent', addresses($m), ['ama@student.test']);

$pass = count(array_filter($results)); $total = count($results);
echo "\n$pass / $total passed\n";
exit($pass === $total ? 0 : 1);
