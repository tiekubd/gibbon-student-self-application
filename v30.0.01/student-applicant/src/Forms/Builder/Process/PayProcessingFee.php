<?php
/*
Gibbon: the flexible, open school platform
Founded by Ross Parker at ICHK Secondary. Built by Ross Parker, Sandra Kuipers and the Gibbon community (https://gibbonedu.org/about/)
Copyright © 2010, Gibbon Foundation
Gibbon™, Gibbon Education Ltd. (Hong Kong)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

namespace Gibbon\Forms\Builder\Process;

use Gibbon\Http\Url;
use Gibbon\Services\Format;
use Gibbon\Comms\EmailTemplate;
use Gibbon\Contracts\Comms\Mailer;
use Gibbon\Contracts\Services\Session;
use Gibbon\Contracts\Services\Payment;
use Gibbon\Forms\Builder\AbstractFormProcess;
use Gibbon\Forms\Builder\ApplicantType;
use Gibbon\Forms\Builder\FormBuilderInterface;
use Gibbon\Forms\Builder\Storage\FormDataInterface;
use Gibbon\Forms\Builder\View\PayProcessingFeeView;
use Gibbon\Forms\Builder\Exception\MissingFieldException;

class PayProcessingFee extends AbstractFormProcess implements ViewableProcess
{
    protected $requiredFields = ['Payment Gateway', 'parent1email'];

    // The contact email field this form uses: parent1email, or the student's email on
    // forms without parent fields. Set by verify(), which runs before Form Builder lists
    // required fields, so that list only shows a field the form is genuinely missing.
    private $contactFields = ['parent1email', 'email'];

    private $session;
    private $payment;
    private $mail;
    private $template;

    public function __construct(Session $session, Payment $payment, Mailer $mail, EmailTemplate $template)
    {
        $this->session = $session;
        $this->payment = $payment;
        $this->mail = $mail;
        $this->template = $template;
    }

    public function getViewClass() : string
    {
        return PayProcessingFeeView::class;
    }

    public function isEnabled(FormBuilderInterface $builder)
    {
        return $builder->hasConfig('formProcessingFee') && $this->checkEnabled($builder);
    }

    public function process(FormBuilderInterface $builder, FormDataInterface $formData)
    {
        $processingFee = $builder->getConfig('formProcessingFee');

        if (!is_numeric($processingFee) || $processingFee <= 0) return;

        $contactEmail = $this->getContactEmail($builder, $formData);
        if (empty($contactEmail)) return;

        $link = Url::fromModuleRoute('Admissions', 'applicationForm_payFee')
            ->withAbsoluteUrl()
            ->withQueryParams([
                'acc'  => $builder->getConfig('accessID', ''),
                'tok'  => $builder->getConfig('accessToken', ''),
                'id'   => $builder->getConfig('identifier', ''),
                'form' => $builder->getFormID(),
            ]);

        // Setup Template 
        $template = $this->template->setTemplateByID($builder->getConfig('formProcessingEmailTemplate'));
        $templateData = array_merge([
            'email'                => $contactEmail,
            'date'                 => Format::date(date('Y-m-d')),
            'link'                 => (string)$link,
            'applicationID'        => intval($builder->getConfig('foreignTableID')),
            'applicationName'      => $builder->getDetail('name'),
            'applicationFee'       => $this->session->get('currency').$processingFee,
            'studentPreferredName' => $formData->get('preferredName'),
            'studentSurname'       => $formData->get('surname'),
            'studentOfficialName'  => $formData->get('officialName'),
            'organisationAdmissionsName'  => $this->session->get('organisationAdmissionsName'),
            'organisationAdmissionsEmail' => $this->session->get('organisationAdmissionsEmail'),
        ], $this->getRecipientNames($builder, $formData));

        // Setup the email
        $this->mail->AddAddress($contactEmail);
        $this->mail->setDefaultSender($template->renderSubject($templateData));
        $this->mail->SetFrom($this->session->get('organisationAdmissionsEmail'), $this->session->get('organisationAdmissionsName'));
        
        $this->mail->renderBody('mail/message.twig.html', [
            'title'  => $template->renderSubject($templateData),
            'body'   => $template->renderBody($templateData),
            'details' => [
                __('Application Form')           => $builder->getDetail('name'),
                __('Application ID')             => intval($builder->getConfig('foreignTableID')),
                __('Application Processing Fee') => $this->session->get('currency').$processingFee,
            ],
            'button' => [
                'url'  => $link,
                'text' => __('Pay Online'),
                'external' => true,
            ],
        ]);

        // Send the email
        $sent = $this->mail->Send();
        $this->setResult($sent);
    }

    public function rollback(FormBuilderInterface $builder, FormDataInterface $formData)
    {
        // Cannot unsend what has been sent...
    }

    public function getRequiredFields() : array
    {
        return array_merge(['Payment Gateway'], $this->contactFields);
    }

    public function verify(FormBuilderInterface $builder, FormDataInterface $formData = null)
    {
        // A contact email is required: Parent 1, or the student on forms without parent fields
        if ($builder->hasField('parent1email')) {
            $this->contactFields = ['parent1email'];
        } elseif ($builder->hasField('email')) {
            $this->contactFields = ['email'];
        } else {
            $this->contactFields = ['parent1email', 'email'];
        }

        if (!$this->payment->isEnabled()) {
            throw new MissingFieldException('Payment Gateway');
        }

        if (!$builder->hasField('parent1email') && !$builder->hasField('email')) {
            throw new MissingFieldException('parent1email,email');
        }
    }

    /**
     * Who receives the processing fee request: the student when the student is applying,
     * otherwise Parent 1; then whichever of those exists; then the admissions account.
     */
    protected function getContactEmail(FormBuilderInterface $builder, FormDataInterface $formData) : string
    {
        $order = ApplicantType::isStudent($builder, $formData) ? ['email', 'parent1email'] : ['parent1email', 'email'];
        foreach ($order as $fieldName) {
            if ($formData->has($fieldName)) return $formData->get($fieldName);
        }

        return $builder->getConfig('accountEmail', '') ?? '';
    }

    /**
     * Names for the email greeting: the student when the student is applying, otherwise
     * Parent 1 (falling back to the student if no parent name was given).
     * The parent* keys are kept so existing templates work unchanged.
     */
    protected function getRecipientNames(FormBuilderInterface $builder, FormDataInterface $formData) : array
    {
        if (!ApplicantType::isStudent($builder, $formData) && ($formData->has('parent1surname') || $formData->has('parent1preferredName'))) {
            return [
                'parentTitle'         => $formData->get('parent1title'),
                'parentPreferredName' => $formData->get('parent1preferredName'),
                'parentSurname'       => $formData->get('parent1surname'),
            ];
        }

        return [
            'parentTitle'         => $formData->get('title', ''),
            'parentPreferredName' => $formData->get('preferredName'),
            'parentSurname'       => $formData->get('surname'),
        ];
    }

    private function checkEnabled(FormBuilderInterface $builder)
    {
        if ($builder->getConfig('mode') == 'process' && $builder->getConfig($this->getProcessName().'Enabled') != 'Y') {
            return false;
        }

        return true;
    }
}
