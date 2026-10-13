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

use Gibbon\Forms\Builder\Storage\FormDataInterface;

/**
 * Who completes an application form, set per form in Form Builder > Active Features >
 * Applicant ("applicantType" in the form config):
 *
 *  - Parent:  a parent or guardian applies for a student (the default, and Gibbon's original behaviour)
 *  - Student: the student applies for themselves; parent sections may still be on the form
 *
 * A school that accepts both creates one form of each.
 *
 * Decides who receives application emails, who the admissions account belongs to, and
 * whether the account's person is used as Parent 1. Kept in one place so the rule cannot
 * drift between files.
 */
class ApplicantType
{
    const PARENT  = 'Parent';
    const STUDENT = 'Student';

    /**
     * The form's setting: Parent or Student. Forms without a setting are Parent.
     */
    public static function getSetting(FormBuilderInterface $builder) : string
    {
        return $builder->getConfig('applicantType', '') == self::STUDENT ? self::STUDENT : self::PARENT;
    }

    /**
     * Is the student completing this application?
     */
    public static function isStudent(FormBuilderInterface $builder, ?FormDataInterface $data = null) : bool
    {
        return self::getSetting($builder) == self::STUDENT;
    }

    /**
     * The admissions account's person to give the form builder as an existing Parent 1,
     * or '' when the student is applying: the account is then the student's own, and a
     * student is never their own parent.
     */
    public static function accountPersonForForm(FormBuilderInterface $builder, ?FormDataInterface $data, $gibbonPersonID) : string
    {
        return !empty($gibbonPersonID) && !self::isStudent($builder, $data) ? (string) $gibbonPersonID : '';
    }
}
