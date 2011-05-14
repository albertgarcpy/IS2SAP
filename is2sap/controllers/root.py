# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
#from tgext.admin.controller import AdminController, AdminConfig
from is2sap.controllers.admin_controlador import AdminController
from is2sap.controllers.desarrollo_controlador import DesarrolloController
from repoze.what import predicates

from is2sap.lib.base import BaseController
from is2sap.model import DBSession, metadata
from is2sap import model
from is2sap.controllers.secure import SecureController
from is2sap.controllers.error import ErrorController
#from is2sap.controllers.mi_admin_config import MiAdminConfig


from tg import tmpl_context, validate
#from is2sap.widgets.usuario_form import crear_usuario_form
from webhelpers import paginate
from repoze.what.predicates import has_permission
#from tg import config



__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the IS2SAP application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    #secc = SecureController()
    admin = AdminController(model, DBSession)
    desa = DesarrolloController(model, DBSession)
    error = ErrorController()

    @expose('is2sap.templates.index')
    def index(self):
        """Handle the front-page."""
        return dict(page='index')

    @expose('is2sap.templates.configura')
    def configura(self):
        """Handle the 'about' page."""
        return dict(page='config')

    @expose('is2sap.templates.desa')
    def desa(self):
        """Display some information about auth* on this application."""
        return dict(page='desa')

    @expose('is2sap.templates.index')
    @require(predicates.has_permission('administracion',  msg=l_('Solo para el Administrador')))
    #@require(predicates.in_group('Administrador', msg=l_('Solo para el administrador')))
    def manage_permission_only(self, **kw):
        """Illustrate how a page for managers only works."""
        return dict(page='managers stuff')

    @expose('is2sap.templates.index')
    @require(predicates.in_group('editor', msg=l_('Solo para editores')))
    def editor_user_only(self, **kw):
        """Illustrate how a page exclusive for the editor works."""
        return dict(page='editor stuff')

    @expose('is2sap.templates.login')
    def login(self, came_from=url('/')):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)

    @expose()
    def post_login(self, came_from='/'):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect('/login', came_from=came_from, __logins=login_counter)
        userid = request.identity['repoze.who.userid']
        flash(_('Bienvenido, %s!') % userid)
        redirect("/index")

    @expose()
    def post_logout(self, came_from=url('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('Hasta luego!'))
        redirect("/index")
