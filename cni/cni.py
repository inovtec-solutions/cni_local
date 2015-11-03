from openerp.osv import fields, osv
import datetime
import logging
import math

_logger = logging.getLogger(__name__)

class product_template(osv.osv):
    _name = "product.template"
    _inherit = "product.template"
    _columns = {
        'sku': fields.char('SKU', size=64, required=True),
        'dimension': fields.char('Dimension', size=64),
    }
product_template()   
    
class asset_requisition(osv.osv):
    """"Asset requisition or tools requistion are the same things"""
    
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        sql = """update project_project set privacy_visibility ='followers' where privacy_visibility ='employees' """
        cr.execute(sql)
        cr.commit()
        return result
    
    def send_request(self, cr, uid, ids, context=None):
        tr_no = self.set_transaction_no(cr, uid, ids,'asset_requisition')
        self.write(cr, uid, ids, {'state':'Waiting','transaction_no':tr_no})
        return
    
    def _get_asset_state(self, cr, uid, team, internal_state):
        state_id = self.pool.get('asset.state').search(cr, uid, [('team','=',team),('name','=',internal_state)])
        if state_id:
            return state_id[0]
        else:
            return False
    
    def approve_request(self, cr, uid, ids, context=None):
        
        denied = ''
        for f in self.browse(cr, uid, ids, context):
            #update 
            line_ids = self.pool.get('asset.requisition.lines').search(cr, uid, [('requisition_id','=',f.id)])
            if line_ids:
                reconcile_rec = self.pool.get('asset.requisition.lines').browse(cr,uid,line_ids)
                for line in reconcile_rec:
                    #first check if this tool is available
                    tool_id = self.pool.get('asset.asset').search(cr, uid,[('id','=',line.name.id)])
                    if tool_id:
                        tool_rec = self.pool.get('asset.asset').browse(cr,uid,tool_id[0])
                        if not tool_rec.issued:
                        #get wharhouse states
                            wh_state =  self.pool.get('asset.state').search(cr, uid, [('team','=',1),('name','=','Issued')])
                            if wh_state:
                                self.pool.get('asset.asset').write(cr,uid,line.name.id,{
                                                           'warehouse_state_id':wh_state[0],
                                                           'user_id':f.employee.id,
                                                           'issued':True})
                                #if asset is updated, update asset requisition
                                self.write(cr, uid, ids[0], {'state':'Approved','aprroved_by':uid})
                            else:
                                raise osv.except_osv(('Error'),("No appropriate state found for Isusuance, eg, Issued"))
                        else:
                            denied += tool_rec.name +"\n" 
            
            else:       
                    
                raise osv.except_osv(('Error'),("Cannot approve with empty list of tools, go back and mention some tools"))
        
        if denied:
             raise osv.except_osv(('Tools not available,reclaim from previous technician and approve this request later on.'),(denied))
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
                                                   'user_id':False,
                                                   'issued':False})
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
    
    def set_transaction_no(self, cr, uid, ids,object):
        string = ""
        if object == 'daily_sale_reconciliation':
            substr = 'DS'
        elif  object == 'asset_requisition':
            substr = 'TR'
        elif object == 'get_client_stock':
            substr = 'CS'
        
        for f in self.browse(cr, uid, ids):
            sql = """SELECT max(id) FROM """+str(object)
            cr.execute(sql)
            numb = cr.fetchone()
            if numb[0] is not None or numb[0] > 0:
                numb = int(numb[0])+1
                
            else:
                numb = 1    
            string  = str(substr)+"-"+str(numb)
        return string
    
    def cancelled_request(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Cancel','aprroved_by':uid})
        return
    def set_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Draft'})
        return
    
    def onchange_project(self, cr, uid, ids, project_id):
        res =  {}
        res['value'] = {'employee': None}
        return res
    
    _name = "asset.requisition"
    _columns = {
        'name':fields.function(_set_name, method=True,  size=256, string='Code',type='char'),
        'transaction_no':fields.char('No.',readonly = True,size = 50), 
        'project': fields.many2one('project.project', 'Project', required=True, ondelete='restrict'),
        'employee': fields.many2one('res.users', 'Required By',domain = [('work_on_task','=',True)], required=True, ondelete='restrict'),
        'date_requisted': fields.date('Date ',required=True),
        'date_returned': fields.date('Date Return',readonly=True),
        'aprroved_by': fields.many2one('res.users', 'Approved By',readonly = True),
        'returned_to': fields.many2one('res.users', 'Returned To',readonly = True),
        'date_approved': fields.date('Approved On', readonly = True,),
        'requisition_lines_ids': fields.one2many('asset.requisition.lines', 'requisition_id', 'Assets',required=True),
        'note': fields.text('Any Note'),
        'state': fields.selection([('Draft','Draft'),
                                   ('Waiting','Waiting'),
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
        'name': fields.many2one('asset.asset', 'Tool',domain=[('issued','=',False)], required = True),      
        'product_qty': fields.float('Quantity',),
        'requisition_id': fields.many2one('asset.requisition','Requisition'),
        'price_unit': fields.float('Unit Price'),
        'total':fields.float('Total'),
        
    }
    _sql_constraints = [  
        ('Duplicated', 'unique (name,requisition_id)', 'Resource Already exists')
    ] 
    _defaults = {
                 
    }
asset_requisition_lines()


class daily_sale_reconciliation(osv.osv):
    """This object store main business process of consumable products sale and its reconciliation"""
    
    def dispatch_product(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids[0], {'state':'Dispatched','dispatched_by':uid})
        
        tr_no = self.pool.get('asset.requisition').set_transaction_no(cr, uid, ids,'daily_sale_reconciliation')
        return
        #update lines state
        reconcile_ids = self.pool.get('sale.reconcile.lines').search(cr, uid, [('dispatch_id','=',ids[0])])
        
        if reconcile_ids:
            price = 0.0
            reconcile_rec = self.pool.get('sale.reconcile.lines').browse(cr,uid,reconcile_ids)
            for line in reconcile_rec:
                rec_product = self.pool.get('product.template').browse(cr,uid,line.name.product_tmpl_id.id)
                price = rec_product.list_price
                
                self.pool.get('sale.reconcile.lines').write(cr,uid,line.id,{'state':'Dispatched','price_unit':price,'total':float(line.dispatch_qty * price)})
        self.write(cr, uid, ids[0], {'state':'Dispatched','dispatched_by':uid,'transaction_no':tr_no})
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
    
    
    def onchange_project(self, cr, uid, ids, project_id):
        res =  {}
        res = {'domain': {'task_id': [('project_id', '=',project_id)]}}
        res['value'] = {'task_id': None, 'employee': None }
        return res
    
    _name = "daily.sale.reconciliation"
    _columns = {
        'name': fields.char('Name', size=64),
        'transaction_no':fields.char('No.',readonly = True,size = 50),
        'project':  fields.many2one('project.project', 'Project', required=True, ondelete='restrict'),
        'task_id':  fields.many2one('project.task', 'Task', required=True, ondelete='restrict'),
        'employee':  fields.many2one('res.users', 'Technician',required=True, domain = [('work_on_task','=',True)], ondelete='restrict'),
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
    
    def onchange_dispatch_qty(self, cr, uid, ids,dispatch_qty,sale_price):
        vals = {}
        total = dispatch_qty * sale_price
        vals['total'] = total
        vals['net_qty'] = dispatch_qty 
        return {'value':vals}
    
    def onchange_returned_qty(self, cr, uid, ids,return_qty,sale_price):
        vals = {}
        for f in self.browse(cr,uid,ids):
            total = (f.dispatch_qty -return_qty ) * sale_price
            vals['total'] = total
            vals['net_qty'] = f.dispatch_qty - return_qty 
            vals['returned_qty'] = return_qty
            update_lines = self.pool.get('sale.reconcile.lines').write(cr, uid, ids, vals) 
        return {'value':vals}
    
    def onchange_product(self, cr, uid, ids,product):
        vals = {}
        rec_product = self.pool.get('product.product').browse(cr,uid,product)
        vals['price_unit'] = rec_product.list_price
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
    
    def onchange_project(self, cr, uid, ids, project_id):
        res =  {}
        rec_project =  self.pool.get('project.project').browse(cr, uid, project_id)
        res = {'domain': {'partner_id': [('id', '=',rec_project.partner_id.id)]}}
        res['value'] = {'partner_id':rec_project.partner_id.id }
        return res
    
       
    _name = "get.client.stock"
    _columns = {
        'name': fields.char('Name', size=64),
        'project':  fields.many2one('project.project', 'Project', required = True, ondelete='restrict'),
        'partner_id': fields.many2one('res.partner', 'Client',readonly = True),
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
    
    def onchange_qty(self, cr, uid, ids, qty,price):
        vals =  {}
        vals['total'] = qty * price
        return {'value':vals}
    
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
        'name': fields.many2one('product.product', 'Tool',domain = [('type','=','product')]),      
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
    
    def load_tasks_and_activities(self,cr,uid,proj_id,project_gen_type):
        """Loads for bell projects only"""
        rec_project_template = self.pool.get('project.generic.template').browse(cr, uid,project_gen_type)
        
        default_task_id = self.pool.get('project.tasks.default').search(cr, uid, [('project_template_id','=',project_gen_type)])
        if default_task_id:
            rec_default_task = self.pool.get('project.tasks.default').browse(cr, uid,default_task_id)
            for d_task in rec_default_task:
                #now create task record in project.task
                task_id = self.pool.get('project.task').create(cr,uid,{
                                            'name':d_task.name,
                                            'project_id':proj_id, 
                                            'planned_hours':d_task.planned_hours,
                                            'user_id':rec_project_template.default_users.id
                                             })
                if task_id:
                    #search default_work activities of task using default task id
                    activity_ids = self.pool.get('project.task.work.default').search(cr, uid, [('task_id','=',d_task.id)])
                    if activity_ids:
                        rec_default_task = self.pool.get('project.task.work.default').browse(cr, uid,activity_ids)
                        for activity in rec_default_task:
                            #now create task activities
                            self.pool.get('project.task.work').create(cr,uid,{
                                            'name':activity.name,
                                            'task_id':task_id, 
                                            'user_id':rec_project_template.default_users.id,
                                            'hours':activity.hours
                                             })
        return
   
    def create(self, cr, uid, vals, context=None, check=False):
        
        result = super(project_project, self).create(cr, uid, vals, context)
        
        for f in self.browse(cr,uid,result):
            vals['template_loaded'] = True
            load = self.load_tasks_and_activities(cr,uid,f.id,f.project_type_template.id)
        return result
   
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        for f in self.browse(cr,uid,ids):
            if 'project_type_template' in vals:
                    self.load_tasks_and_activities(cr,uid,f.id,vals['project_type_template'])
                    vals['template_loaded'] = True
        result = super(project_project, self).write(cr, uid, ids, vals, context)
        return result
    
    def unlink(self, cr, uid, ids, context=None):
        result = False
        admin = self.check_user_group(cr,uid,'CNI Admin')
        if admin:
            result = super(project_project, self).unlink(cr, uid, ids, context)
        else:
            raise osv.except_osv(('Not Allowed'),("You are not authorized to delete project, Contact your service provider."))
        return result
    
    def onchange_projecttype(self, cr, uid, ids,type):
        vals = {}
        if type=='Pre-Assembly':
            partner = self.pool.get('res.partner').search(cr, uid, [('name','=','BELL'),])
            if partner:
                vals['partner_id'] = partner[0]
            return { 'value':vals  }
        else:
            return {} 
    
    def check_user_group(self, cr, uid,required_group):
        sql="""select id
                from res_groups 
                inner join res_groups_users_rel
                on res_groups.id=res_groups_users_rel.gid
                where res_groups_users_rel.uid="""+str(uid)+""" and res_groups.name = '"""+str(required_group)+"""'"""
        cr.execute(sql)
        res=cr.fetchone()
        if res:
            return res[0]
        else:
            return False
    
    def is_access_restricted(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids)
        sql="""select id
                from res_groups_users_rel
                 inner join res_groups
                on res_groups.id=res_groups_users_rel.gid
                where res_groups_users_rel.uid="""+str(uid)+""" and res_groups.name in ('Group CNI Technician')"""
        cr.execute(sql)
        res=cr.fetchone()

        for f in records:
            if res:
                result[f.id] = True
            else:
                result[f.id] = False
        

        return result
    
    _name = 'project.project'
    _inherit ='project.project'
    _columns = {
    'restrict_access':fields.function(is_access_restricted, method=True, string='Restrict Access',type='boolean'),
    'partner_id': fields.many2one('res.partner', 'Client', readonly = True),
    'excel_project': fields.boolean('Issued',readonly=True),
    'upload_file': fields.binary('File'),
    'project_planned_hours': fields.float('Project Hours'),
    'project_types':fields.selection([('Pre-Assembly', 'Pre-Assembly'),('General', 'General')], 'Project Location'),
    'project_type_template':fields.many2one('project.generic.template', 'Type', required = True),
    'consumable': fields.one2many('daily.sale.reconciliation', 'project', 'Consumable'),
    'stockable': fields.one2many('get.client.stock', 'project', 'Stockable'),
    'tools_used': fields.one2many('asset.requisition', 'project', 'Tools'),
    'material_ids': fields.one2many('project.material', 'name', 'Material'),
    'project_id': fields.char('Project ID', size=64),
    'priority': fields.char('Priority', size=64),
    'primevera_id': fields.char('PrimaveraID', size=64),
    'actv_desc': fields.char('Activity Desc', size=64),
    'network_id': fields.char('Network', size=64),
    'wbs': fields.char('WBS', size=64),
    'site_code': fields.date('Site Code'),
    'template_loaded':fields.boolean("Template Loaded"),
    'status': fields.char('SC Status', size=64),
    }
    _defaults = {
                 'project_types':lambda *a:'General',
                 'excel_project':lambda *a:False,
                 'privacy_visibility': 'followers',
    }
project_project()

class project_material(osv.osv):
    """This object is created for projecdt utility. will work only for pre assembly project, populate data from csv file using import"""
    _name = 'project.material'
    _columns = {
    'name': fields.many2one('project.project', 'Project'),
    'network_id': fields.char('Network', size=64),
    'item': fields.char('Item(H)', size=64),
    'activity_description': fields.char('Activity Description', size=64),
    'plant': fields.float('Plant'),
    'transaction_no': fields.integer('Transaction No.'),
    'mat_desc': fields.char('Matr Desc(W)', size=64),
    'req_quantiity':fields.integer('Required MtQuantity(AL)'),
    'shiping_date': fields.date('Shipping Date(R)'),
    'material_req_date': fields.date('Required MtDate(Q)'),
    'delivery_pa': fields.char('Delivery PA#(BL)', size=64),
    'delivery_date': fields.date('Delivery PA Date(BO)'),
    'pa_gi_doc': fields.char('PA-GI Document(BP)', size=64),
    'gr_doc_pa': fields.char('GR-Document-PA', size=64),
    'gi_date': fields.char('PA GI Date(BQ)', size=64),
    'po_pa': fields.char('PO(P-A)#(BS)', size=64),
    'remarks': fields.char('Remarks', size=64),
    }
    _defaults = {
    }
project_material()

class project_work(osv.osv):
    
    def check_constrains(self, cr, uid, vals,task_id):
        rec_task = self.pool.get('project.task').browse(cr,uid,task_id)
        if 'date' in vals:
            deadline = rec_task.date_deadline
            if deadline:
                if vals['date'] > deadline:
                    raise osv.except_osv(('Not Allowed'),("Work date must be within Task deadline."))
        if rec_task.planned_hours:
            planned_hours = rec_task.planned_hours
        else:
            planned_hours = 0
        
        override_limit = False
        
        if 'override_hrs' in vals:
            if vals['override_hrs']:
                override_limit = True
        elif rec_task.override_hrs:
            override_limit = True
        if 'hours' in vals:
            #calculate all work time spent for this task i.e milestone
            work_ids = self.pool.get('project.task.work').search(cr, uid, [('task_id','=',task_id)])
            if work_ids:
                work_rec = self.pool.get('project.task.work').browse(cr,uid,work_ids)
                total_spent_hrs = 0
                for spent_hour in work_rec:
                    total_spent_hrs = total_spent_hrs + spent_hour.hours
                #compare
#                 if float(planned_hours - total_spent_hrs) < vals['hours'] and not override_limit:
#                     warning = "This Task has total hours "+str(planned_hours - total_spent_hrs)," (Out of  " +str(planned_hours)+") Avaible.\n Your work hours must be not greater than "+str(planned_hours - total_spent_hrs)+"\n"+str(vals['hours'])+"Can't be accumudated.  "
#                     raise osv.except_osv(('Work Hour Exceeds'),('Reset Spent Hours'))
#                 else:
#                     return True
        return True
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        for f in self.browse(cr,uid,result):
            check = self.check_constrains(cr, uid, vals,f.task_id.id)
        return result
  
     
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        result = False
        for f in self.browse(cr,uid,ids):
            check = self.check_constrains(cr, uid, vals,f.task_id.id)
            if check:
                result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        return result
     
    def unlink(self, cr, uid, ids, context=None):
        result = super(osv.osv, self).unlink(cr, uid, ids, context)
        return result 
    
    
    def is_access_restricted(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids, context) 
        sql="""select id
                from inner res_groups_users_rel
                 inner res_groups
                on res_groups.id=res_groups_users_rel.gid
                where res_groups_users_rel.uid="""+str(uid)+""" and res_groups.name in ('Group CNI Technician')"""
        cr.execute(sql)
        res=cr.fetchone()
        for f in records:
            if res:
                result[f.id] = True
            else:
                result[f.id] = False
        return result

    
    _name = "project.task.work"
    _description = "Project Task Work"
    _inherit ='project.task.work'
    _columns = {
        'name': fields.char('Task Summary'),
        'restrict_access':fields.function(is_access_restricted, method=True,  size=256, string='Restrict Access',type='boolean'),
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


#---------------------------------------------------------------------------------------------------------------------------------

class project_generic_template(osv.osv):
    """This stores generic project templates"""
    _name = 'project.generic.template'
    _columns = {
    'name': fields.char(string = 'Name',size = 150, required =  True),
    'desc':fields.char(string = 'Desc',size = 150),
    'default_task_ids':fields.one2many('project.tasks.default','project_template_id','Tasks'),
    'default_users':fields.many2one('res.users','Default Worker',required = True)
    }
project_generic_template()




class project_tasks_default(osv.osv):
    
    """"""
    
    def check_hour_exceed(self, cr, uid, task_id,task_name,task_hours):
        
        work_hrs = 0
        work_ids = self.pool.get('project.task.work.default').search(cr, uid, [('task_id','=',task_id)])
        if work_ids:
            rec_w = self.pool.get('project.task.work.default').browse(cr, uid, task_id)
            for w in rec_w:
                work_hrs = work_hrs + w.hours
            if work_hrs > task_hours:
               raise osv.except_osv(('Hours Exceeds'),("Sum of work hours in  Task "+str(task_name)+" Exceeds than Task planed hours\n Go to Task " +str(task_name)+" and reset its activity hours."))
            else:
                return False
    
    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        
        hours_exceeds = True
        for f in self.browse(cr, uid, ids):
            hours_exceeds = self.check_hour_exceed(cr, uid, ids[0],f.name,f.planned_hours)
        if not hours_exceeds:
            result = super(osv.osv, self).write(cr, uid, ids, vals, context)
        else:
            result = False
        return result
    
    def create(self, cr, uid, vals, context=None, check=True):
        result = super(osv.osv, self).create(cr, uid, vals, context)
        hours_exceeds = self.check_hour_exceed(cr, uid, result,vals['name'],vals['planned_hours'])
        return result
    
    _name = 'project.tasks.default'
    _columns = {
    'name': fields.char('Task(Template)',size = 100,required = True),
    'planned_hours': fields.float('Initially Planned Hours', help='Estimated time to do the task, usually set by the project manager when the task is in draft state.'),
    'project_template_id': fields.many2one('project.generic.template', 'Project'),
    'project_stage':fields.char('Stage',size = 150),
    'project_task_work_ids': fields.one2many('project.task.work.default', 'task_id', 'Task Activity'),
    'user_id': fields.many2one('res.users', 'Done by'),
    }
project_tasks_default()

class project_task_work_default(osv.osv):
    """This object stores project  tasks work activities, task are associated with task"""
    _name = 'project.task.work.default'
    _columns = {
    'task_id': fields.many2one('project.tasks.default', 'Task'),
    'name':fields.char('Activity',size = 150,required=True,),
    'user_id': fields.many2one('res.users', 'Will be Assigned to'),
    'hours': fields.float('Time to be Spent'),
    }
project_task_work_default()

#-------------------------------------------------------------------------------------------------------------------------

class res_users(osv.osv):
    """This object inherited res_users adding a columns 'Can be assign milstone, this will filter this user'"""
    _name = "res.users"
    _description = "Project Task Work"
    _inherit ='res.users'
    _columns = {
        'work_on_task': fields.boolean('Can be assigned Tasks'),
            }

res_users()

#-----------------------------------------------------------------------------------------------------------------------------

class project_task(osv.osv):
    """This object inherited res_users adding a columns 'Can be assign milstone, this will filter this user'"""
    def is_access_restricted(self, cr, uid, ids, context={}, arg=None, obj=None):
        result = {}
        records = self.browse(cr, uid, ids)
        sql="""select id
                from res_groups_users_rel
                 inner join res_groups
                on res_groups.id=res_groups_users_rel.gid
                where res_groups_users_rel.uid="""+str(uid)+""" and res_groups.name in ('Group CNI Technician')"""
        cr.execute(sql)
        res=cr.fetchone()

        for f in records:
            if res:
                result[f.id] = True
            else:
                result[f.id] = False
        return result

    
    _name = "project.task"
    _description = "Project Task Work"
    _inherit ='project.task'
    _columns = {
        'user_id': fields.many2one('res.users', 'Assigned to', domain=[('work_on_task', '=',True)], select=True, track_visibility='onchange'),
        'override_hrs':fields.boolean('Override Task Hours'),
        'consumable_products_ids': fields.one2many('daily.sale.reconciliation', 'task_id', 'Stockables'),
        'restrict_access':fields.function(is_access_restricted, method=True, string='Restrict Access',type='boolean'),
            }

project_task()

#---------------------------------- time sheeet --------------------------------------------------------------------------------------------------------

class hr_timesheet_sheet(osv.osv):
    _name = "hr_timesheet_sheet.sheet"
    _inherit = "hr_timesheet_sheet.sheet"
    _description="Timesheet"
    
    def onchange_date(self, cr, uid, ids, this_date,choice):
        """it received from amd to date from timesheet"""
        print "this date",this_date
        print "today", datetime.date.today()
        vals = {}
        if choice == 'compare_date_from':
            if this_date:
                if str(this_date) > str(datetime.date.today()):
                    vals['date_from'] = None
        elif choice == 'compare_date_to':
            if str(this_date) > str(datetime.date.today()):
                vals['date_to'] = None
        return {'value':vals}
    
    _columns = {}
    _defaults = {
        'date_from' : '',
        'date_to' : '',
    }

hr_timesheet_sheet()
  #-------------------------------------------------------------------------------------------------------------------------
  
