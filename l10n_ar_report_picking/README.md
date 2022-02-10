# PrePrint Picking of Argentina

## Settings

Create an Account Journal and check "Es Diario de Remitos Electrónicos". Then, create a Sequence with Step 1 and Next Number according to the next issue of Picking to validate.

Load the List of Electronic Pickings CAI with CAI Due Date on table "Lista de Remitos Disponibles".

## Validate Electronic Picking

In order to Validate a Stock Picking like a Electronic Picking, search the Tab "Remito" inside a Stock Picking Out Type. Make sure Account Journal is load on "Diario de Remitos Electrónicos" field (normally is loaded by default). Click the button "Validar Remito".

## Mass Import for CAI

You can add a list of CAI with the Due Date in CSV Format. The file must not have headers, and just two cols: first the CAI number and then the Due Date of CAI number.

## Automatic Remove of Due CAI

In order of remove the expired numbers of CAI, you can use the button "Eliminar CAI Vencidos" inside Account Journal of Electronic Pickings.

## Warning

By regulation, it is not allowed to print a Pre-Printed Picking on a sheet that is not from the approved printing company. You will probably need to edit the PDF to match the press sheet (report_stock_picking.xml file).

## Contributors

* Exemax
* Codize

## Maintainer

This module is maintained by the Exemax-Codize team.
