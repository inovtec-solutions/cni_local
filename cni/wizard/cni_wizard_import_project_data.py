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
        row = 7
            
        while row <= rows:
<<<<<<< HEAD
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
            
=======
            
            if row >= 137:
                break 
            
            transaction_no = str(worksheet.cell_value(row, 1))
            project_id_excel = str(worksheet.cell_value(row, 2))
             
            _logger.info("Transaction No.: %r, Project ID: %r", transaction_no, project_id_excel)
            
            try:
                float(transaction_no) # for int, long and float
            except ValueError:
                row += 1    
                continue
            
            _logger.info("___________________________%r", transaction_no)
            
            if worksheet.cell_value(row, 31) == 'P-A':
                _logger.info("_______________P-A____________%r", worksheet.cell_value(row, 31))
            
            
                project_exist = self.pool.get('project.project').search(cr, uid, [('project_id','=',project_id_excel)])
                if project_exist:
                    project_id = project_exist[0]
                    _logger.info("_______________if project____________%r", worksheet.cell_value(row, 31))
            
                else:
                    project_id = self.pool.get('project.project').create(cr, uid, {
                        'name': worksheet.cell_value(row, 9),
                        'project_types': 'Pre-Assembly',
                        'project_id': worksheet.cell_value(row, 2),
                        'network': worksheet.cell_value(row, 4),
                        'actv_desc': worksheet.cell_value(row, 6),
                        'wbs': worksheet.cell_value(row,11),
                        'delivery_pa': worksheet.cell_value(row, 63), }, context=context)            


                material_exist = self.pool.get('project.material').search(cr, uid, [('name','=',project_id),('transaction_no','=',worksheet.cell_value(row, 1))])
                
                shiping_date = str(worksheet.cell_value(row,46))
                if shiping_date.strip() == "":
                    shiping_date = None
                else:
                    shiping_date = shiping_date.replace(".", "/")
                
                material_req_date = str(worksheet.cell_value(row, 16))
                if material_req_date.strip() == "":
                    material_req_date = None
                else:
                    material_req_date = material_req_date.replace(".", "/")
                    
                if material_exist:
                    material_id = material_exist[0]
                    self.pool.get('project.material').write(cr, uid, material_id, {
                        'material_req_date': material_req_date,
                        'mat_desc': worksheet.cell_value(row, 22),
                        'req_quantiity': worksheet.cell_value(row,37),
                        'shiping_date': shiping_date,
                        'delivery_pa': worksheet.cell_value(row,63),
                        'pa_gi_doc': worksheet.cell_value(row,67)}, context=context)
                else:
                    self.pool.get('project.material').create(cr, uid, {
                        'name': project_id,
                        'transaction_no': worksheet.cell_value(row, 1),
                        'material_req_date': material_req_date,
                        'mat_desc': worksheet.cell_value(row, 22),
                        'req_quantiity': worksheet.cell_value(row,37),
                        'shiping_date': shiping_date,
                        'delivery_pa': worksheet.cell_value(row,63),
                        'pa_gi_doc': worksheet.cell_value(row,67)}, context=context)            

>>>>>>> 3215b8971b148634e27dfd3053a92210f76aad39
            row += 1
        return {}

cni_import_project_data()

