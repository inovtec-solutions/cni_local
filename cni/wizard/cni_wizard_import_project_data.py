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
            project_id_excel = str(worksheet.cell_value(row, 2))
            project_id_excel = project_id_excel.strip()
            
            if project_id_excel == "":
                row += 1    
                continue
            
            
            if worksheet.cell_value(row, 31) == 'P-A':
                _logger.info("_______________P-A____________%r", worksheet.cell_value(row, 31))
            
            
                project_exist = self.pool.get('project.project').search(cr, uid, [('project_id','=',project_id_excel)])
                if project_exist:
                    project_id = project_exist[0]
                    _logger.info("_______________IF Project____________%r", project_id_excel)
            
                else:
                    project_id = self.pool.get('project.project').create(cr, uid, {
                        'name': project_id_excel,
                        'project_types': 'Pre-Assembly',
                        'project_id': project_id_excel,
                        'network': worksheet.cell_value(row, 4),
                        'status': worksheet.cell_value(row, 10),
                        'actv_desc': worksheet.cell_value(row, 6),
                        'wbs': worksheet.cell_value(row,11),
                        'delivery_pa': worksheet.cell_value(row, 63), }, context=context)            

                material_desc = str(worksheet.cell_value(row, 22))
                material_desc = material_desc.strip()
                
                network = str(worksheet.cell_value(row, 4))
                network = network.strip()
                        
                item = str(worksheet.cell_value(row, 7))
                item = item.strip()
                
                _logger.info("_______________Material Description/ Item____________%r%r", material_desc,item)
                 
                material_exist = self.pool.get('project.material').search(cr, uid, [('name','=',project_id),('mat_desc','=',material_desc),('item','=',item)])
                
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
                    _logger.info("_______________IF Material____________%r", material_id)
                    self.pool.get('project.material').write(cr, uid, material_id, {
                        'material_req_date': material_req_date,
                        'req_quantiity': worksheet.cell_value(row,37),
                        'shiping_date': shiping_date,
                        'delivery_pa': worksheet.cell_value(row,63),
                        'pa_gi_doc': worksheet.cell_value(row,67)}, context=context)
                else:
                    self.pool.get('project.material').create(cr, uid, {
                        'name': project_id,
                        'network': network,
                        'item': worksheet.cell_value(row, 7),
                        'material_req_date': material_req_date,
                        'mat_desc': worksheet.cell_value(row, 22),
                        'req_quantiity': worksheet.cell_value(row,37),
                        'shiping_date': shiping_date,
                        'delivery_pa': worksheet.cell_value(row,63),
                        'pa_gi_doc': worksheet.cell_value(row,67)}, context=context)            

            row += 1
        return {}

cni_import_project_data()

