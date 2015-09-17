from openerp.osv import fields, osv
import datetime
import logging

_logger = logging.getLogger(__name__)

class product_template(osv.osv):
    _name = "product.template"
    _inherit = "product.template"
    _columns = {
        'sku': fields.char('SKU', size=64, required=True),
        'dimension': fields.char('Dimension', size=64),
    }
    
class asset_requisition(osv.osv):
    
    def send_request(self, cr, uid, ids, context=None):
        tr_no = self.set_transaction_no(cr, uid, ids)
        self.write(cr, uid, ids, {'state':'Open','transaction_no':tr_no})
        return
    
    def _get_asset_state(self, cr, uid, team, internal_state):
        _logger.info("=in called method team========================================== : %r", team)
        _logger.info("=in called method internal_state========================================== : %r", internal_state)
        state_id = self.pool.get('asset.state').search(cr, uid, [('team','=',team),('name','=',internal_state)])
        if state_id:
            return state_id[0]
        else:
            return False
    
    def approve_request(self, cr, uid, ids, context=None):
        
        for f in self.browse(cr, uid, ids, context):
            #update 
            line_ids = self.pool.get('asset.requisition.lines').search(cr, uid, [('requisition_id','=',f.id)])
            if line_ids:
                reconcile_rec = self.pool.get('asset.requisition.lines').browse(cr,uid,line_ids)
                _logger.info("=reconcile_rec========================================== : %r", reconcile_rec)
                for line in reconcile_rec:
                    #get wharhouse states
                    wh_state =  self.pool.get('asset.state').search(cr, uid, [('team','=',1),('name','=','Issued')])
                    if wh_state:
                        _logger.info("=wh_state========================================== : %r", wh_state[0])
                        self.pool.get('asset.asset').write(cr,uid,line.name.id,{
                                                   'warehouse_state_id':wh_state[0],
                                                   'user_id':f.employee.id})
                        #if asset is updated, update asset requisition
                        self.write(cr, uid, ids[0], {'state':'Approved','aprroved_by':uid})
                    else:
                        _logger.info("=No appropriate state found e.g Issued")
        return
        
    def return_asset(self, cr, uid, ids, context=None):
        
        for f in self.browse(cr, uid, ids, context):
            #update 
            line_ids = self.pool.get('asset.requisition.lines').search(cr, uid, [('requisition_id','=',f.id)])
            if line_ids:
                reconcile_rec = self.pool.get('asset.requisition.lines').browse(cr,uid,line_ids)
                _logger.info("=reconcile_rec========================================== : %r", reconcile_rec)
                for line in reconcile_rec:
                    #get wharhouse states
                    wh_state =  self.pool.get('asset.state').search(cr, uid, [('team','=',1),('name','=','Available')])
                    if wh_state:
                        _logger.info("=wh_state========================================== : %r", wh_state[0])
                        self.pool.get('asset.asset').write(cr,uid,line.name.id,{
                                                   'warehouse_state_id':wh_state[0],
                                                   'user_id':f.employee.id})
                        #if asset is updated, update asset requisition
                        self.write(cr, uid, ids[0], {'state':'Returned','returned_to':uid,'date_returned':datetime.date.today()})
                    else:
                        _logger.info("=No appropriate state found e.g Issued")
        return
        
    def _set_name(self, cr, uid, ids, name, args, context=None):
        result = {}
       
        for f in self.browse(cr, uid, ids, context=context):
            result[f.id] = f.project.name + " (" + f.employee.name+")"
        return result
    
    def set_transaction_no(self, cr, uid, ids):
        string = ""
        for f in self.browse(cr, uid, ids):
            sql = """SELECT max(id) FROM asset_requisition WHERE state <> 'Draft'"""
            cr.execute(sql)
            numb = cr.fetchone()
            if numb:
                numb = int(numb[0])+1
                
            else:
                numb = 1    
            string  = "TR-"+str(numb)
        return string
    
    def cancelled_request(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Cancel','aprroved_by':uid})
        return
    
    _name = "asset.requisition"
    _columns = {
        'name':fields.function(_set_name, method=True,  size=256, string='Code',type='char'),
        'transaction_no':fields.char('No.',readonly = True,size = 50), 
        'project':  fields.many2one('project.project', 'Project', required=True, ondelete='restrict'),
        'employee':  fields.many2one('hr.employee', 'Required By', required=True, ondelete='restrict'),
        'date_requisted':  fields.date('Date ',required=True),
        'date_returned':  fields.date('Date Return',readonly=True),
        'aprroved_by':  fields.many2one('res.users', 'Approved By'),
        'returned_to':  fields.many2one('res.users', 'Returned To'),
        'date_approved':  fields.date('Approved On'),
        'requisition_lines_ids': fields.one2many('asset.requisition.lines', 'requisition_id', 'Assets'),
        'note': fields.text('Any Note'),
        'state': fields.selection([('Draft','New'),
                                   ('Open','Waiting'),
                                   ('Approved','Approved'),
                                   ('Cancel', 'Cancel'),
                                   ('Returned', 'Returned')
                                  ],
                                  'Status', required=True),
    }
    
    _defaults = {
                 'state':'Draft'
                 
    }
    
class asset_requisition_lines(osv.osv):
    """ Asset Requiston lines """
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        return result
  
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
     
    def unlink(self, cr, uid, ids, context=None):
        result = super(osv.osv, self).unlink(cr, uid, ids, context)
        return result 
    
    
    
    _name = 'asset.requisition.lines'
    _description = "This object store fee types"
    _columns = {
        'name': fields.many2one('asset.asset', 'Tool'),      
        'product_qty': fields.float('Quantity'),
        'requisition_id': fields.many2one('asset.requisition','Requisition'),
        'price_unit': fields.float('Unit Price'),
        'total':fields.float('Total'),
        
    }
    _sql_constraints = [  
        ('Fee Exisits', 'unique (name,requisition_id)', 'Resource Already exists')
    ] 
    _defaults = {
                 
    }
asset_requisition_lines()


class daily_sale_reconciliation(osv.osv):
    """This object store main business process of consumable products sale and its reconciliation"""
    
    def dispatch_product(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Dispatched','dispatched_by':uid})
        #update lines state
        reconcile_ids = self.pool.get('sale.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
        
        if reconcile_ids:
            price = 0.0
            reconcile_rec = self.pool.get('sale.reconcile.lines').browse(cr,uid,reconcile_ids)
            for line in reconcile_rec:
                rec_product = self.pool.get('product.template').browse(cr,uid,line.name.product_tmpl_id.id)
                price = rec_product.list_price
                _logger.info("=price========================================== : %r", price)
                
                self.pool.get('sale.reconcile.lines').write(cr,uid,line.id,{'state':'Dispatched','price_unit':price,'total':float(line.dispatch_qty * price)})
        return
    
    def confirm_sale(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Confirmed','confirmed_by':uid,'date_confirmed':datetime.date.today()})
    
        #update status in sales lines
        reconcile_ids = self.pool.get('sale.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
                
        if reconcile_ids:
            reconcile_rec = self.pool.get('sale.reconcile.lines').browse(cr,uid,reconcile_ids)
            for line in reconcile_rec:
                rec_product = self.pool.get('product.template').browse(cr,uid,line.name.product_tmpl_id.id)
                price = rec_product.list_price
                self.pool.get('sale.reconcile.lines').write(cr,uid,line.id,{'state':'Confirmed'})
                
        return
    
    def cancel_sale(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Cancel','confirmed_by':uid})
        #update status in sales lines
        reconcile_ids = self.pool.get('sale.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
        if reconcile_ids:
            for prd_id in reconcile_ids:
                self.pool.get('sale.reconcile.lines').write(cr,uid,prd_id,{'state':'Cancel,',})
        return
    
    def _calculate_saleline_netsum(self, cr, uid, ids, name, args, context=None):
        result = {}
        sum = 0
        for f in self.browse(cr,uid,ids):
            reconcile_ids = self.pool.get('sale.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
            if reconcile_ids:
                rec_sale_lines = self.pool.get('sale.reconcile.lines').browse(cr, uid, reconcile_ids)
                for amount in rec_sale_lines:
                    sum = sum + amount.total
                result[f.id] = sum
        return result
    
    _name = "daily.sale.reconciliation"
    _columns = {
        'name': fields.char('Name', size=64),
        'project':  fields.many2one('project.project', 'Project', required=True, ondelete='restrict'),
        'employee':  fields.many2one('hr.employee', 'Technician', required=True, ondelete='restrict'),
        'date_dispatched':  fields.date('Date',required=True),
        'date_confirmed':  fields.date('Date Confirm',readonly=True),
        'dispatched_by':  fields.many2one('res.users', 'Dispatch By',readonly=True),
        'confirmed_by':  fields.many2one('res.users', 'Confirm By',readonly=True),
        'sale_reconcile_lines_ids': fields.one2many('sale.reconcile.lines', 'dispatch_id', 'Products'),
        'total_amount': fields.function(_calculate_saleline_netsum,string = 'Total Amount.',type = 'float',method = True),      
        'note': fields.text('Special Note'),
        'state': fields.selection([('Draft','New'),
                                   ('Dispatched','Open'),
                                   ('Confirmed','Confirmed'),
                                   ('Cancel', 'Cancel'),
                                  ],
                                  'Status', required=True),
    }
    
    _defaults = {
                 'state':'Draft'
                 
    }
    
class sale_reconcile_lines(osv.osv):
    """This object store main business process of consumable products sale and its reconciliationlines """
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        return result
  
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
     
    def onchange_returned_product(self, cr, uid, ids,return_qty):
        vals = {}
        for f in self.browse(cr,uid,ids):
            disp_qty = f.dispatch_qty
            price = f.price_unit
            net_amount = (disp_qty - return_qty)*price
            vals['total'] = net_amount
            vals['net_qty'] = disp_qty - return_qty
            update_lines = self.pool.get('sale.reconcile.lines').write(cr, uid, ids, {
                       'returned_qty':return_qty,
                       'net_qty':vals['net_qty'],
                       'total':vals['total'],
                       }) 
        return {'value':vals}
    
    def unlink(self, cr, uid, ids, context=None):
        result = super(osv.osv, self).unlink(cr, uid, ids, context)
        return result 
    
    _name = 'sale.reconcile.lines'
    _description = "This object store sale reconcile"
    _columns = {
        'name': fields.many2one('product.product', 'Product'),      
        'dispatch_qty': fields.float('Dispatched', required=True),
        'returned_qty': fields.float('Returned'),
        'net_qty': fields.float('Used', readonly=True),
        'dispatch_id': fields.many2one('daily.sale.reconciliation','Sale Reconciliation'),
        'price_unit': fields.float('Unit Price'),
        'total':fields.float('Total'),
        'state': fields.selection([('Draft','New'),
                                   ('Dispatched','Open'),
                                   ('Confirmed','Confirmed'),
                                   ('Cancel', 'Cancel'),
                                  ],
                                  'Status', required=True),
        
    }
   
    _defaults = {'state':'Draft'}
sale_reconcile_lines()

#--------------------------------------- Clinets sotckable ----------------------------------------------------

class get_client_stock(osv.osv):
    
    def add_to_stock(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'Waiting'})
        return
    
    def get_transaction_no(self, cr, uid, team, internal_state):
        return False
    
    def confirm_add_to_stock(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'In_Stock'})
        return
    def stock_out(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'Waiting_Stockout'})
        return
    
    def confirm_stock_out(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'Waiting_Stockout'})
        return
    
    def cancelled_stock_reception(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Cancel'})
        return
    
    def _calculate_stock_netsum(self, cr, uid, ids, name, args, context=None):
        result = {}
        sum = 0
        for f in self.browse(cr,uid,ids):
            reconcile_ids = self.pool.get('sale.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
            if reconcile_ids:
                rec_sale_lines = self.pool.get('sale.reconcile.lines').browse(cr, uid, reconcile_ids)
                for amount in rec_sale_lines:
                    sum = sum + amount.total
                result[f.id] = sum
        return result
    
    _name = "get.client.stock"
    _columns = {
        'name': fields.char('Name', size=64),
        'project':  fields.many2one('project.project', 'Project', required=True, ondelete='restrict'),
        'partner_id': fields.many2one('res.partner', 'Client'),
        'date_received':  fields.date('Date',required=True),
        'location_id': fields.many2one('stock.location', 'Warehouse', required=True, domain=[('usage','<>','view')]),
        'aprroved_by':  fields.many2one('res.users', 'Approved By' ,readonly = True),
        'stock_lines_ids': fields.one2many('client.stock.lines', 'stock_parent_id', 'Stock Lines'),
        'note': fields.text('Any Note'),
        'state': fields.selection([('Draft','New'),
                                   ('Waiting','Waiting'),
                                   ('In_Stock','In Stock'),
                                    ('Waiting_Stockout','Waiting Stockout'),
                                    ('Stockout','Stockout'),
                                   ('Cancel', 'Cancel'),
                                  ],
                                  'State', required=True),
    }
    
    _defaults = {
                 'state':'Draft'
                 
    }
    
class client_stock_lines(osv.osv):
    """ Clinets stock lines """
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        return result
  
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
     
    def unlink(self, cr, uid, ids, context=None):
        result = super(osv.osv, self).unlink(cr, uid, ids, context)
        return result 
    
    def onchange_returned_product(self, cr, uid, ids,return_qty):
        vals = {}
        for f in self.browse(cr,uid,ids):
            disp_qty = f.dispatch_qty
            vals['total'] = disp_qty *f.price
            update_lines = self.pool.get('client.stock.lines').write(cr, uid, ids, {
                       'net_qty':vals['net_qty'],
                       'total':vals['total'],
                       }) 
        return {'value':vals}
    
    _name = 'client.stock.lines'
    _description = "Clint stock lines"
    _columns = {
        'name': fields.many2one('product.product', 'Tool'),      
        'product_qty': fields.float('Quantity'),
        'stock_parent_id': fields.many2one('get.client.stock','Requisition'),
        'price_unit': fields.float('Unit Price'),
        'total':fields.float('Total'),
        
    }
   
    _defaults = {
                 
    }
client_stock_lines()
#-------------------------------------------------------------------------------------------------------------------------------

#----------------------------------- inherited project.project------------------------------------------------------------------

class project_project(osv.osv):
    """Extended project.project through inheritance"""
    
    def onchange_projecttype(self, cr, uid, ids,type):
        vals = {}
        if type=='Pre-Assembly':
            partner = self.pool.get('res.partner').search(cr, uid, [('name','=','BELL'),])
            if partner:
                vals['partner_id'] = partner[0]
            return { 'value':vals  }
        else:
            return {} 
    
    _name = 'project.project'
    _inherit ='project.project'
    _columns = {
    'partner_id': fields.many2one('res.partner', 'Client'),
    'project_types':fields.selection([('Pre-Assembly', 'Pre-Assembly'),('General', 'General')], 'Project Type'),
    'consumable': fields.one2many('daily.sale.reconciliation', 'project', 'Consumable'),
    'stockable': fields.one2many('get.client.stock', 'project', 'Stockable'),
    'tools_used': fields.one2many('asset.requisition', 'project', 'Tools'),
    'material_ids': fields.one2many('project.material', 'name', 'Material'),
    'project_id': fields.char('Project ID', size=64),
    'priority': fields.char('Priority', size=64),
    'primevera_id': fields.char('PrimaveraID', size=64),
    'actv_desc': fields.char('Activity Desc', size=64),
    'wbs': fields.char('WBS', size=64),
    'site_code': fields.date('Site Code'),
    'status': fields.char('SC Status', size=64),
    }
    _defaults = {
                 'project_types':lambda *a:'General'
    }
project_project()

class project_material(osv.osv):
    """This object is created for projecdt utility. will work only for pre assembly project, populate data from csv file using import"""
    _name = 'project.material'
    _columns = {
    'name': fields.many2one('project.project', 'Project'),
    'network': fields.char('Network(E)', size=64),
    'item': fields.char('Item(H)', size=64),
    'activity_description': fields.char('Activity Description', size=64),
    'transaction_no': fields.integer('Transaction No.'),
    'mat_desc': fields.char('Matr Desc(W)', size=64),
    'req_quantiity':fields.integer('Required MtQuantity(AL)'),
    'shiping_date': fields.date('Shipping Date(R)'),
    'material_req_date': fields.date('Required MtDate(Q)'),
    'delivery_pa': fields.char('Delivery PA#(BL)', size=64),
    'delivery_date': fields.date('Delivery PA Date(BO)'),
    'pa_gi_doc': fields.char('PA-GI Document(BP)', size=64),
    'gi_date': fields.char('PA GI Date(BQ)', size=64),
    'po_pa': fields.char('PO(P-A)#(BS)', size=64),
    'network': fields.char('Network', size=64),
    'mat_desc': fields.char('Matr Desc', size=64),
    'item': fields.char('Item', size=64),
    'req_quantiity':fields.integer('Required Quantity'),
    'shiping_date': fields.date('Shipping Date'),
    'material_req_date': fields.date('Required Date'),
    'delivery_pa': fields.char('Delivery PA', size=64),
    'delivery_date': fields.date('Delivery Date'),
    'pa_gi_doc': fields.char('PA-GI Document', size=64),
    'gi_date': fields.char('Delivery PA', size=64),
    'remarls': fields.char('Remarks', size=64),
    }
    _defaults = {
    }
project_material()

class project_work(osv.osv):
    """This object inherites project_task_work object ony one filed is change work summary of acutal module is change to task summary"""
    _name = "project.task.work"
    _description = "Project Task Work"
    _inherit ='project.task.work'
    _columns = {
        'name': fields.char('Task Summary'),
            }

project_work()


#----------------------------------------------------------------------------------------------------------
#-------------------------------------- inherited hr.employee-----------------------------------------------
class hr_employee(osv.osv):
    """Extended hr.employee through inheritance"""
    _name = 'hr.employee'
    _inherit ='hr.employee'
    _columns = {
    'tools_acquired': fields.one2many('asset.requisition', 'employee', 'Tools'),
    'project_assigned': fields.one2many('daily.sale.reconciliation', 'project', 'Projects')
    }
hr_employee()



#------------------------------Asset Inherited--------------------------------------------------------------------
class asset_asset(osv.osv):
    """Extended asset.assete through inheritance"""
    _name = 'asset.asset'
    _inherit ='asset.asset'
    _columns = {
    'asset_reservation_ids': fields.one2many('emp.tools.reservation', 'tool_to_reserve', 'Reservation'),
    }
hr_employee()


#----------------------------------------------------------------------------------------------------------
#-------------------------------------- Employee Tools Reservation-----------------------------------------------
class emp_tools_reservation(osv.osv):
    """This objects stores record of tools reserved by an employee"""
    _name = 'emp.tools.reservation'
    _columns = {
    'name': fields.many2one('hr.employee', 'Employee'),
    'tool_to_reserve': fields.many2one('asset.asset', 'Tool'),
    'date_from': fields.date('Date From'),
    'date_to': fields.date('Date To'),
    'reserved_by': fields.char('Reserved_by', size=64, readonly=True),
    'issued': fields.boolean('Issued',readonly=True),
    }
emp_tools_reservation()

#---------------------------------------------------------------------------------------------------------

class res_company(osv.osv):
    """Extended company through inheritance"""
    _name = 'res.company'
    _inherit ='res.company'
    _columns = {
    'project_types_ids': fields.one2many('project.types', 'name', 'Assets'),
    
    }
res_company()
#---------------------------------------------------------------------------------------------------------------------------------

class project_types(osv.osv):
    """This objects stores record of tools reserved by an employee"""
    _name = 'project.types'
    _columns = {
    'name': fields.many2one('res.company', 'Types', readonly = True),
    'project_types':fields.selection([('Pre-Assembly', 'Pre-Assembly'),('Installation', 'Installation'),('General', 'General')], 'Project Types'),
    'project_stages_ids': fields.one2many('project.stages', 'name', 'Project Stages'),
    }
project_types()

class project_stages(osv.osv):
    """This objects stores record of tools reserved by an employee"""
    _name = 'project.stages'
    _columns = {
    'name': fields.many2one('project.types', 'Types'),
    'project_stage':fields.char('Stage',size = 150),
    'stage_task_ids': fields.one2many('project.stage.task', 'name', 'Tasks'),
    }
project_stages()

class project_stage_task(osv.osv):
    """This object stores project stage tasks, task are associated with stages"""
    _name = 'project.stage.task'
    _columns = {
    'name': fields.many2one('project.stages', 'Stage'),
    'task':fields.char('Task',size = 150),
    }
project_stage_task()



   
