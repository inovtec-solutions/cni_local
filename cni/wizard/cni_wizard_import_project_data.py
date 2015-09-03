from openerp.osv import fields, osv
import datetime
import xlrd
import logging

_logger = logging.getLogger(__name__)

class cni_import_project_data(osv.osv_memory):
    """Use this wizard to Import Project Data from the excel file"""
    _name = "cni.import.project.data"
    _description = "Import Project Data From Excel"
    _columns = {
              'file_name': fields.char('File', size=300, required=True),
             }
    _defaults = {
        'file_name': '/home/odoo/project_data.xls',
    }
    
    def import_project_data(self, cr, uid, ids, context=None):
        current_obj = self.browse(cr, uid, ids, context=context)
        workbook = xlrd.open_workbook(current_obj[0].file_name)
        worksheet = workbook.sheet_by_name('project_data')
        rows = worksheet.nrows - 1
        cells = worksheet.ncols - 1
        row = 1
        
        while row <= rows:
            _logger.info("Excel Rows : %r", worksheet.cell_value(row, 3))
            print "rows: ", rows
            row += 1
            continue;
            project_exist = self.pool.get('project.project').search(cr, uid, [('network','=',worksheet.cell_value(row, 4)),('transaction_no','=',worksheet.cell_value(row, 1))])
            
            if worksheet.cell_value(row, 31) == 'P-A':
                if project_exist:
                    project_id = project_exist[0]
                else:
                    project_id = self.pool.get('project.project').create(cr, uid, {
                        'project_id': worksheet.cell_value(row, 2),
                        'network': worksheet.cell_value(row, 4),
                        'actv_desc': worksheet.cell_value(row, 6),
                        'wbs': worksheet.cell_value(row,11),
                        'delivery_pa': worksheet.cell_value(row, 63), }, context=context)            


                material_exist = self.pool.get('project.material').search(cr, uid, [('name','=',project_id),('transaction_no','=',worksheet.cell_value(row, 1))])
                if material_exist:
                    material_id = material_exist[0]
                    self.pool.get('project.material').write(cr, uid, material_id, {
                        'material_req_date': worksheet.cell_value(row, 16),
                        'mat_desc': worksheet.cell_value(row, 22),
                        'req_quantiity': worksheet.cell_value(row,37),
                        'shiping_date': worksheet.cell_value(row,46),
                        'delivery_pa': worksheet.cell_value(row,63),
                        'pa_gi_doc': worksheet.cell_value(row,67)}, context=context)
                else:
                    material_id = self.pool.get('project.material').create(cr, uid, {
                        'name': material_id,
                        'transaction_no': worksheet.cell_value(row, 1),
                        'material_req_date': worksheet.cell_value(row, 16),
                        'mat_desc': worksheet.cell_value(row, 22),
                        'req_quantiity': worksheet.cell_value(row,37),
                        'shiping_date': worksheet.cell_value(row,46),
                        'delivery_pa': worksheet.cell_value(row,63),
                        'pa_gi_doc': worksheet.cell_value(row,67)}, context=context)            

            row += 1
        return {}

cni_import_project_data()

