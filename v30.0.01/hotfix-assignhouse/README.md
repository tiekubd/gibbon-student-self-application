# Auto House Assign hotfix (Gibbon v30.0.01)

`AssignHouse` passes `$formData->has('gibbonPersonIDStudent')` (= `true` = ID 1) to
`userGateway->update()`, so every accepted student's house is written to person 1 and the
student gets none. Already fixed upstream in the development branch (uses `get()`); this is
the same two-word fix for v30.0.01 only. Drop this file once the school upgrades past v30.

| File | Before (stock v30.0.01) | After |
|---|---|---|
| `src/Forms/Builder/Process/AssignHouse.php` | `79aa45d3413d2d0b9795576fb52b1a25` | `0149bd714156aafe7ed29b8a17bec2b7` |

Tested on the official v30.0.01 bundle: stock gives the house to person 1 and none to the
student; fixed gives the student the house and leaves person 1 alone.

`repair_houses.sql` restores houses for students already accepted (preview first, then apply).
Person 1's house is NOT reset by the script: check whether that account should have a house.
