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

namespace Gibbon\Forms\Builder;

use Gibbon\Domain\User\UserGateway;
use Gibbon\Domain\User\FamilyGateway;
use Gibbon\Forms\Builder\Storage\FormDataInterface;
use Gibbon\Contracts\Services\Session;
use Gibbon\Domain\Admissions\AdmissionsApplicationGateway;
use Gibbon\Domain\Admissions\AdmissionsAccountGateway;

class FormPrefill
{
    protected $session;
    protected $userGateway;
    protected $familyGateway;

    protected $prefillable = [];
    protected $prefilled = false;
    protected $accountEmail = '';

    public function __construct(Session $session, UserGateway $userGateway, FamilyGateway $familyGateway)
    {
        $this->session = $session;
        $this->userGateway = $userGateway;
        $this->familyGateway = $familyGateway;
    }

    public function isPrefilled()
    {
        return $this->prefilled;
    }

    /**
     * The email address of the admissions account filling in this form. Used to suggest
     * the student's email on forms without parent fields (student self-applications).
     *
     * @param string|null $email
     * @return self
     */
    public function setAccountEmail(?string $email)
    {
        $this->accountEmail = $email ?? '';

        return $this;
    }

    /**
     * Prefill values from the most recent application form attached to this account
     *
     * @param AdmissionsApplicationGateway $admissionsApplicationGateway
     * @param array $recentApplication
     * @return self
     */
    public function loadApplicationData(AdmissionsAccountGateway $admissionsAccountGateway, AdmissionsApplicationGateway $admissionsApplicationGateway, string $gibbonFormID, ?string $accessID, ?string $accessToken)
    {
        // Check if this account can prefill application form data
        $accountCheck = $admissionsAccountGateway->getAccountByAccessToken($accessID, $accessToken);
        if (empty($accountCheck)) {
            return $this;
        }

        $recentApplication = $admissionsApplicationGateway->selectMostRecentApplicationByContext($gibbonFormID, 'gibbonAdmissionsAccount', $accountCheck['gibbonAdmissionsAccountID'])->fetch();

        if (!empty($recentApplication)) {
            $this->prefillable = json_decode($recentApplication['data'] ?? '', true);
        }

        return $this;
    }

    /**
     * Prefill parent and family data, if this account has access to it.
     *
     * @param AdmissionsAccountGateway $admissionsAccountGateway
     * @param string $gibbonPersonID
     * @param string $accessID
     * @param string $accessToken
     * @return self
     */
    public function loadPersonalData(AdmissionsAccountGateway $admissionsAccountGateway, ?string $gibbonPersonID, ?string $accessID, ?string $accessToken)
    {
        if (empty($gibbonPersonID)) return $this;

        $canAccessAccount = $canAccessData = false;

        // Check if this account can prefill user data
        $accountCheck = $admissionsAccountGateway->getAccountByAccessToken($accessID, $accessToken);
        $canAccessAccount = !empty($accountCheck) && $gibbonPersonID == $accountCheck['gibbonPersonID'];
        $canAccessData = (!empty($accountCheck)) || ($this->session->get('gibbonPersonID') == $gibbonPersonID);

        if ($canAccessAccount && $canAccessData) {
            // Load and prefill values for Parent 1
            $person = $this->userGateway->getSafeUserData($gibbonPersonID);
            foreach ($person ?? [] as $fieldName => $value) {
                $this->prefillable['parent1'.$fieldName] = $value;
            }

            // Load and prefill values for the family
            $family = $this->familyGateway->getByID($accountCheck['gibbonFamilyID'] ?? '');
            foreach ($family ?? [] as $fieldName => $value) {
                if ($fieldName == 'name') $fieldName = 'familyName';
                $this->prefillable[$fieldName] = $value;
            }
        }

        return $this;
    }

    /**
     * Only prefill fields that are marked as prefillable, and don't already exist.
     *
     * @param FormBuilderInterface $formBuilder
     * @param FormDataInterface $formData
     * @param array $values
     * @return self
     */
    public function prefill(FormBuilderInterface $formBuilder, FormDataInterface $formData, $pageNumber, &$values)
    {
        // Only prefill fields that are marked as prefillable, and don't already exist
        foreach ($this->prefillable as $fieldName => $value) {
            if ($formData->exists($fieldName)) continue;
            if (!$formBuilder->hasField($fieldName)) continue;

            $field = $formBuilder->getField($fieldName);
            if ($field['pageNumber'] != $pageNumber && $pageNumber > 0) continue;
            if (empty($field['prefill']) || $field['prefill'] == 'N') continue;

            $values[$fieldName] = $value;
            $this->prefilled = true;
        }

        // Student self-applications (no parent fields): the account email belongs to the applicant,
        // so offer it as the student's email. It stays editable, e.g. for a separate school address.
        $hasParentFields = $formBuilder->hasField('parent1surname') || $formBuilder->hasField('parent1preferredName') || $formBuilder->hasField('parent1email');
        if (!$hasParentFields && !empty($this->accountEmail) && $formBuilder->hasField('email') && !$formData->exists('email') && empty($values['email'])) {
            $field = $formBuilder->getField('email');
            if ($field['pageNumber'] == $pageNumber || $pageNumber <= 0) {
                $values['email'] = $this->accountEmail;
                $this->prefilled = true;
            }
        }

        return $this;
    }
}
