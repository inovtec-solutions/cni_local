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
            project_exist = self.pool.get('project.project').search(cr, uid, [('network','=',worksheet.cell_value(row, 3)),('transaction_no','=',worksheet.cell_value(row, 3))])
            
            if project_exist:
                self.pool.get('project.project').write(cr, uid, project_exist[0], {
                    'network': worksheet.cell_value(row, 1),
                    'priority': worksheet.cell_value(row, 1),
                    'primevera_id': worksheet.cell_value(row, 2),
                    'actv_desc': worksheet.cell_value(row, 3),
                    'wbs': worksheet.cell_value(row, 4),
                    'delivery_pa': worksheet.cell_value(row,5),
                    'status': worksheet.cell_value(row,6),
                    'site_code': worksheet.cell_value(row,7),
                     }, context=context)
            else:
                self.pool.get('project.project').create(cr, uid, {
                    'transaction_no': worksheet.cell_value(row, 1),
                    'network': worksheet.cell_value(row, 2),
                    'priority': worksheet.cell_value(row, 3),
                    'primevera_id': worksheet.cell_value(row, 4),
                    'actv_desc': worksheet.cell_value(row, 5),
                    'wbs': worksheet.cell_value(row, 6),
                    'delivery_pa': worksheet.cell_value(row,7),
                    'status': worksheet.cell_value(row,6),
                    'site_code': worksheet.cell_value(row,8),
                    }, context=context)
            
            row += 1
        return {}

cni_import_project_data()

