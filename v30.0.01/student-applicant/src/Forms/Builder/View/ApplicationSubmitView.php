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

namespace Gibbon\Forms\Builder\View;

use Gibbon\Forms\Form;
use Gibbon\Services\Format;
use Gibbon\Contracts\Services\Session;
use Gibbon\Forms\Builder\AbstractFormView;
use Gibbon\Forms\Builder\Storage\FormDataInterface;

class ApplicationSubmitView extends AbstractFormView
{
    protected $session;
    
    public function __construct(Session $session)
    {
        $this->session = $session;
    }
    
    public function getHeading() : string
    {
        return 'Applicant';
    }

    public function getName() : string
    {
        return __('Application Status');
    }

    public function getDescription() : string
    {
        return '';
    }

    public function configure(Form $form)
    {
        $options = [
            'Parent'  => __('A parent or guardian, for a student'),
            'Student' => __('The student, for themselves'),
        ];

        $row = $form->addRow();
            $row->addLabel('applicantType', __('Who completes this application?'))->description(__('Decides who receives application emails and who the admissions account belongs to. Parent sections can still be included when the student applies. To accept both, create one form of each and name them so applicants can tell them apart.'));
            $row->addSelect('applicantType')->fromArray($options);
    }

    public function display(Form $form, FormDataInterface $data)
    {

    }
}
