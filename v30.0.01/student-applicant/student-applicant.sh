#!/bin/bash
# Students applying for themselves, and billing the student directly, for Gibbon v30.0.01
# Run from the Gibbon webroot:   bash student-applicant.sh check | backup | verify | rollback
#   check    - confirms the files are stock v30.0.01 BEFORE upload, and shows the database step (changes nothing)
#   backup   - copies each existing file to <file>.v30bak (changes nothing else)
#   verify   - confirms the uploaded files AFTER upload, and that sql/finance_student.sql has been run
#   rollback - restores the .v30bak copies and removes the new ApplicantType.php
#              (then run sql/finance_student_rollback.sql to undo the database step)
# Format: file | before (stock v30.0.01) | after
FILES='
modules/Admissions/applicationForm.php|2cb8e503612ab106e2628d847a6fdd28|93f30dcaa61f13bb4e8a5036ab672a94
modules/Admissions/applicationFormProcess.php|d664a7f0821907eee242ee98e377df13|ae06f4c68d4797039cc0fce2d63a761a
modules/Admissions/applications_manage_accept.php|f0f15ae6133481af7a9c71a3761a925b|b30a4c1010b90f5bec379db201a8dc93
modules/Admissions/applications_manage_acceptProcess.php|94a60123ecc76725d55017164035cd8b|febbc24d90034fd2c7b9dad40b7a181c
modules/Admissions/applications_manage_add.php|feab3e6c973bad1f385f731ddf620442|96c08e0b65c7f855e858728c41d337c4
modules/Admissions/applications_manage_addProcess.php|9caf3fd870ab264a464c0b3dbedbcda0|7b20e60dd4be699c8773baffcdf5b5ae
modules/Admissions/applications_manage_edit.php|f5634305bdde1aec3819eb8f6ca64291|2c74b515e3fcb56d655982668be2eac3
modules/Admissions/applications_manage_editProcess.php|c68edc88f86bd757b097ef991666a83f|ecb33f8bd3c68dc5defbb85f11e6d1de
src/Forms/Builder/ApplicantType.php|-|62106efe8b6081fdffa9be61a3d2ed2e
src/Forms/Builder/Fields/FamilyFields.php|c588ad5c7d7c6869bbb661b791356dc4|696acc9557cd57279404ebf19c1e189b
src/Forms/Builder/Fields/FinanceFields.php|ac1364b614f1e8e1e7009e43bba616e6|a8ec5b42bc116d2364e0c6ddc737fbfb
src/Forms/Builder/FormPrefill.php|bd798ce3cc756b33169dd3ab0a4b26e3|0fd469b5499fafd6c85086f401d7e3a7
src/Forms/Builder/Process/ApplicationSubmit.php|dc5cf5f4827419c599f58edd9901ab99|89d9c0fe256019c10a2f598667b34948
src/Forms/Builder/Process/AssignHouse.php|79aa45d3413d2d0b9795576fb52b1a25|0149bd714156aafe7ed29b8a17bec2b7
src/Forms/Builder/Process/CreateInvoicee.php|63efd961031f16c6ef1f03b26e4df623|e59aba3af49d453c0a1bc824fb27e1b6
src/Forms/Builder/Process/PayProcessingFee.php|867bf80c84a085a663de5ca6632e0c7d|4aef44e5baf660f20bde50504dc97877
src/Forms/Builder/Process/SendAcceptanceEmail.php|d6952df5cc9f3845c608052e7103b4e4|e0da356866fec91af5cc4145f51df5ce
src/Forms/Builder/Process/SendSubmissionEmail.php|6e3f32c8ca52a177e2b447102a1124bf|4800a6bd8b7fbf33cbd14bdb8e52ba7e
src/Forms/Builder/View/ApplicationSubmitView.php|8fc1e2ef147346291af8d9222f4de602|aca4f0fcfe35d428df1f502c340f624d
src/Forms/Builder/View/PayProcessingFeeView.php|97ce0898be485aa066b0e942b31e7563|98abd13cfbb5f4b9057de964da28c006
src/Forms/Builder/View/SendAcceptanceEmailView.php|46e805c62f5930c482fe64abc1fce1e0|a590a907956f52a0ccdb293cf15a135f
src/Forms/Builder/View/SendSubmissionEmailView.php|4779fd87ac6a5accb5b5df00ffd493b9|4a95e399308218caaaefd22042e1118c
modules/Activities/activities_paymentProcessBulk.php|d925ed21c3b2806b9f07d6d6683ddb52|825e9d285ddbf84e40b78c9a4ef65f18
modules/Data Updater/data_finance.php|ac784758877e9934c9ee87cbe3c95fc1|075461dafa65397afef0bd0ca2785b4f
modules/Finance/invoicees_manage.php|37c8e95aa6f4f0e4fe12bf9fc4a9552e|007b8f588e73d22eaea69997d7a9ceb0
modules/Finance/invoicees_manage_edit.php|ce57e7853ca1ec979a0c1a31439881bc|b8a3dc9fd8474eade99e06fe891d8d4b
modules/Finance/invoices_manage_addProcess.php|d1d960ebfb70a988cb48ab4dd2e6699a|d47fc872246428f9daa507807e2f614a
modules/Finance/invoices_manage_processBulk.php|34dc4a1138defb4b33d54472512ae3ef|cb30cd3dc62f277831ab6a63d75aeab7
modules/Finance/invoices_payOnlineProcess.php|0cabab29237de8170156d641276e2994|0e29707fc475249ba131ad68de5da3ff
modules/Finance/moduleFunctions.php|aa50a8b8c9e1ecbd33acb8b6c8a161bd|6aab0928fbb4d9631631922ac5a8b8df
modules/Finance/src/Forms/FinanceFormFactory.php|3e8c1990a5046beeda76f18476bd66cb|fedb950fc48e900e33dbec838f850d4c
'
[ -f gibbon.php ] && [ -d modules/Admissions ] || { echo "Run this from the Gibbon webroot (the folder with gibbon.php)."; exit 1; }
sum() { [ -f "$1" ] && md5sum "$1" | cut -c1-32 || echo "-"; }

# Has sql/finance_student.sql been run? Reads the database details from config.php.
dbstate() {
  php -r '
    include "config.php";
    try {
      $pdo = new PDO("mysql:host=$databaseServer;dbname=$databaseName;charset=utf8mb4", $databaseUsername, $databasePassword);
      $n = $pdo->query("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND COLUMN_NAME=\"invoiceTo\" AND TABLE_NAME IN (\"gibbonFinanceInvoicee\",\"gibbonFinanceInvoice\",\"gibbonFinanceInvoiceeUpdate\") AND COLUMN_TYPE LIKE \"%Student%\"")->fetchColumn();
      echo $n == 3 ? "done" : ($n == 0 ? "not run" : "partly run ($n of 3 tables)");
    } catch (Exception $e) { echo "unknown (could not connect)"; }' 2>/dev/null || echo "unknown"
}

bad=0; n=0
while IFS='|' read -r f before after; do
  [ -z "$f" ] && continue
  n=$((n+1))
  case "$1" in
    check)
      now=$(sum "$f")
      if [ "$now" = "$before" ]; then echo "OK         $f"
      elif [ "$now" = "$after" ]; then echo "ALREADY    $f (new version already there)"
      else echo "UNEXPECTED $f ($now)"; bad=1; fi ;;
    backup)
      if [ "$before" = "-" ]; then echo "NEW FILE   $f (nothing to back up)"
      elif [ -f "$f.v30bak" ]; then echo "EXISTS     $f.v30bak (left as is)"
      else cp -p "$f" "$f.v30bak" && echo "BACKED UP  $f"; fi ;;
    verify)
      now=$(sum "$f")
      if [ "$now" = "$after" ]; then echo "OK         $f"; else echo "MISMATCH   $f ($now)"; bad=1; fi ;;
    rollback)
      if [ "$before" = "-" ]; then rm -f "$f" && echo "REMOVED    $f"
      elif [ -f "$f.v30bak" ]; then cp -p "$f.v30bak" "$f" && echo "RESTORED   $f"
      else echo "NO BACKUP  $f"; bad=1; fi ;;
    *) echo "Usage: bash student-applicant.sh check|backup|verify|rollback"; exit 1 ;;
  esac
done <<< "$FILES"

case "$1" in
  check)
    echo "DATABASE   sql/finance_student.sql: $(dbstate)" ;;
  verify)
    db=$(dbstate)
    if [ "$db" = "done" ]; then echo "DATABASE   sql/finance_student.sql: done"
    else echo "DATABASE   sql/finance_student.sql: $db -- run it now, before anyone chooses Student billing"; bad=1; fi ;;
  rollback)
    echo "DATABASE   files restored; now run sql/finance_student_rollback.sql" ;;
esac
[ $bad = 0 ] && echo "All $n files: done." || echo "Some files need attention (see above)."
