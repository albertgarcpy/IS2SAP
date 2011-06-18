"""Admin Controller"""
from sqlalchemy.orm import class_mapper
import inspect
from tg.controllers import TGController
from tg.decorators import with_trailing_slash, override_template, expose
from tg.exceptions import HTTPNotFound
from tg import config as tg_config
from mi_admin_config import MiAdminConfig as AdminConfig 
from tgext.crud import CrudRestController

engine = 'genshi'
try:
    import chameleon.genshi
    import pylons.config
    if 'renderers' in pylons.config and 'chameleon_genshi' in pylons.config['renderers']:
        engine = 'chameleon_genshi'
except ImportError:
    pass

from repoze.what.predicates import in_group
from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tg import tmpl_context, validate
from webhelpers import paginate
from repoze.what.predicates import has_permission
from repoze.what import predicates

from is2sap.lib.base import BaseController
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
from is2sap.controllers.usuario_controlador import UsuarioController
from is2sap.controllers.tipo_item_controlador import TipoItemController
from is2sap.controllers.atributo_controlador import AtributoController
from is2sap.controllers.proyecto_controlador import ProyectoController
from is2sap.controllers.rol_controlador import RolController
from is2sap.controllers.fase_controlador import FaseController
from is2sap.controllers.permiso_controlador import PermisoController
from is2sap.controllers.linea_base_controlador import LineaBaseController


class AdminController(TGController):
    """
    A basic controller that handles User Groups and Permissions for a TG application.
    """
    #allow_only = in_group('managers')
    allow_only = has_permission('administracion',
                                msg=l_('Solo para usuarios con permiso "administracion"'))
    default_index_template = "genshi:is2sap.templates.admin_principal"
		
    #Administracion
    usuario = UsuarioController()
    rol = RolController()
    permiso = PermisoController()
    proyecto = ProyectoController()
    fase = FaseController()
    tipo_item = TipoItemController()
    linea_base = LineaBaseController()
    atributo = AtributoController()


    def __init__(self, models, session, config_type=None, translations=None):
        super(AdminController, self).__init__()
        if translations is None:
            translations = {}
        if config_type is None:
            config = AdminConfig(models, translations)
        else:
            config = config_type(models, translations)

        if config.allow_only:
            self.allow_only = config.allow_only

        self.config = config
        self.session = session

        self.default_index_template = ':'.join((tg_config.default_renderer, self.index.decoration.engines.get('text/html')[1]))
        if self.config.default_index_template:
            self.default_index_template = self.config.default_index_template

    @with_trailing_slash
    @expose('tgext.admin.templates.index')
    def index(self):
        #overrides the template for this method
        original_index_template = self.index.decoration.engines['text/html']
        new_engine = self.default_index_template.split(':')
        new_engine.extend(original_index_template[2:])
        self.index.decoration.engines['text/html'] = new_engine
        return dict(models=[model.__name__ for model in self.config.models.values()])

    def _make_controller(self, config, session):
        m = config.model
        Controller = config.defaultCrudRestController
        class ModelController(Controller):
            model        = m
            table        = config.table_type(session)
            table_filler = config.table_filler_type(session)
            new_form     = config.new_form_type(session)
            new_filler   = config.new_filler_type(session)
            edit_form    = config.edit_form_type(session)
            edit_filler  = config.edit_filler_type(session)
            allow_only   = config.allow_only
        menu_items = None
        if self.config.include_left_menu:
            menu_items = self.config.models
        return ModelController(session, menu_items)

    @expose()
    def _lookup(self, model_name, *args):
        model_name = model_name[:-1]
        try:
            model = self.config.models[model_name]
        except KeyError:
            raise HTTPNotFound().exception
        config = self.config.lookup_controller_config(model_name)
        controller = self._make_controller(config, self.session)
        return controller, args

    @expose()
    def lookup(self, model_name, *args):
        return self._lookup(model_name, *args)
