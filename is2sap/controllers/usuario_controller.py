# -*- coding: utf-8 -*-
"""Usuario Controller"""
from is2sap.model import DBSession, metadata, Usuario
from is2sap.widgets.usuario_form import crear_usuario_form
from tgext.crud import CrudRestController
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.formbase import EditableForm
from sprox.fillerbase import EditFormFiller


__all__ = ['UsuarioController']


class UsuarioTable(TableBase):
    __model__ = Usuario
#    __omit_fields__ = ['password','_password','id','email']
usuario_table = UsuarioTable(DBSession)

class UsuarioTableFiller(TableFiller):
    __model__ = Usuario
   
usuario_table_filler = UsuarioTableFiller(DBSession)

class UsuarioEditForm(EditableForm):
    __model__ = Usuario
#    __omit_fields__ = ['id']
usuario_edit_form = UsuarioEditForm(DBSession)

class UsuarioEditFiller(EditFormFiller):
    __model__ = Usuario
usuario_edit_filler = UsuarioEditFiller(DBSession)

class UsuarioController(CrudRestController):
    model = Usuario
    table = usuario_table
    table_filler = usuario_table_filler
    new_form = crear_usuario_form
    edit_form = crear_usuario_form
    edit_filler = usuario_edit_filler
