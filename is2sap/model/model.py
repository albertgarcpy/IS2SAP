# -*- coding: utf-8 -*-
"""
Auth* related model.

This is where the models used by :mod:`repoze.who` and :mod:`repoze.what` are
defined.

It's perfectly fine to re-use this definition in the IS2SAP application,
though.

"""
import os
from datetime import datetime
import sys
try:
    from hashlib import sha1
except ImportError:
    sys.exit('ImportError: No module named hashlib\n'
             'If you are on python2.4 this library is not part of python. '
             'Please install it. Example: easy_install hashlib')

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, synonym

from is2sap.model import DeclarativeBase, metadata, DBSession


try:
    from sqlalchemy.dialects.postgresql import *
except ImportError:
    from sqlalchemy.databases.postgres import *

__all__ = ['Proyecto', 'Fase', 'TipoItem', 'Atributo', 'EstadoFase', 'Rol', 'Usuario', 'Group', 'Permission']


#{ Association tables


# This is the association table for the many-to-many relationship between
# groups and permissions. This is required by repoze.what.
group_permission_table = Table('tg_group_permission', metadata,
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('tg_permission.permission_id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)


# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships. It's required by repoze.what.
user_group_table = Table('tg_user_group', metadata,
    Column('user_id', Integer, ForeignKey('Usuario.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
    Column('group_id', Integer, ForeignKey('tg_group.group_id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
)


# Relacion entre mucho a mucho Proyecto Usuario
Proyecto_Usuario = Table('Proyecto_Usuario', metadata,
    Column('id_proyecto', INTEGER(), ForeignKey('Proyecto.id_proyecto', 
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column('id_usuario', INTEGER(), ForeignKey('Usuario.id',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False),
)

# Relacion entre mucho a mucho Proyecto Rol
Proyecto_Rol = Table('Proyecto_Rol', metadata,
    Column('id_proyecto', INTEGER(), ForeignKey('Proyecto.id_proyecto',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column('id_rol', INTEGER(), ForeignKey('Rol.id_rol',
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False)
)

Fase = Table('Fase', metadata,
    Column('id_fase', INTEGER(), primary_key=True, nullable=False),
    Column('id_estado_fase', INTEGER(), ForeignKey('Estado_Fase.id_estado_fase'), nullable=False),
    Column('id_proyecto', INTEGER(), ForeignKey('Proyecto.id_proyecto'), nullable=False),
    Column('nombre', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False),
    Column('descripcion', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False)),
    Column('numero_fase', INTEGER(), nullable=False),
)




#{ The auth* model itself



class Proyecto(DeclarativeBase):
    __tablename__ = 'Proyecto'

    #column definitions
    id_proyecto = Column('id_proyecto', INTEGER(), primary_key=True, nullable=False)
    id_usuario = Column('id_usuario', INTEGER(), ForeignKey('Usuario.id'), nullable=False)
    nombre = Column('nombre', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False)
    descripcion = Column('descripcion', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False)
    fecha = Column('fecha', DATE(), nullable=False)
    iniciado = Column('iniciado', BOOLEAN(create_constraint=True, name=None), nullable=False)


    #Tiene una relacion con la tabla Usuario
    relacion_usuario = relation('Usuario', secondary=Proyecto_Usuario, backref='proyectos')


class Fase(DeclarativeBase):
    __table__ = Fase


    #relation definitions
    relacion_estado_fase = relation('EstadoFase', backref='fases')
    relacion_proyecto = relation('Proyecto', backref='fases')



class TipoItem(DeclarativeBase):
    __tablename__ = 'Tipo_Item'

    #column definitions
    id_tipo_item = Column('id_tipo_item', INTEGER(), primary_key=True, nullable=False)
    id_fase = Column('id_fase', INTEGER(), ForeignKey('Fase.id_fase'), nullable=False)
    nombre = Column('nombre', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False)
    descripcion = Column('descripcion', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False))

    #relation definitions
    relacion_fase = relation('Fase', backref='tipoitems')



class Atributo(DeclarativeBase):
    __tablename__ = 'Atributos'

    #column definitions
    descripcion = Column('descripcion', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False))
    id_atributo = Column('id_atributo', INTEGER(), primary_key=True, nullable=False)
    id_tipo_item = Column('id_tipo_item', INTEGER(), ForeignKey('Tipo_Item.id_tipo_item'), nullable=False)
    nombre = Column('nombre', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False)
    tipo = Column('tipo', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False)

    #relation definitions
    relacion_tipo_item = relation('TipoItem', backref='atributos')




class EstadoFase(DeclarativeBase):
    __tablename__ = 'Estado_Fase'

    #column definitions
    id_estado_fase = Column('id_estado_fase', INTEGER(), primary_key=True, nullable=False)
    nombre_estado = Column('nombre_estado', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False)

    #relation definitions



class Rol(DeclarativeBase):
    __tablename__ = 'Rol'

    #column definitions
    descripcion = Column('descripcion', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False))
    id_rol = Column('id_rol', INTEGER(), primary_key=True, nullable=False)
    nombre = Column('nombre', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False)



class Group(DeclarativeBase):
    """
    Group definition for :mod:`repoze.what`.

    Only the ``group_name`` column is required by :mod:`repoze.what`.

    """

    __tablename__ = 'tg_group'

    #{ Columns

    group_id = Column(Integer, autoincrement=True, primary_key=True)

    group_name = Column(Unicode(16), unique=True, nullable=False)

    display_name = Column(Unicode(255))

    created = Column(DateTime, default=datetime.now)

    #{ Relations

    users = relation('Usuario', secondary=user_group_table, backref='groups')

    #{ Special methods

    def __repr__(self):
        return ('<Group: name=%s>' % self.group_name).encode('utf-8')

    def __unicode__(self):
        return self.group_name

    #}


# The 'info' argument we're passing to the email_address and password columns
# contain metadata that Rum (http://python-rum.org/) can use generate an
# admin interface for your models.



class Usuario(DeclarativeBase):

    __tablename__ = 'Usuario'

    #column definitions
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    nombre = Column(u'nombre', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False)
    apellido = Column(u'apellido', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None,    _warn_on_bytestring=False), nullable=False)
    nombre_usuario = Column(u'nombre_usuario', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, 
unicode_error=None, _warn_on_bytestring=False), unique=True, nullable=False)
    _password = Column(u'password', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False), nullable=False)
    direccion = Column(u'direccion', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False))
    telefono = Column(u'telefono', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False))
    email = Column(u'e-mail', VARCHAR(length=None, convert_unicode=False, assert_unicode=None, unicode_error=None, _warn_on_bytestring=False))


    #{ Special methods
    def __repr__(self):
        return ('<Usuario: nombre=%r, email=%r, nombre_usuario=%r>' % (
                self.nombre, self.email, self.nombre_usuario)).encode('utf-8')

    def __unicode__(self):
        return self.nombre_usuario or self.nombre

    #{ Getters and setters

    @property
    def permissions(self):
        """Return a set with all permissions granted to the user."""
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

    @classmethod
    def by_email_address(cls, email):
        """Return the user object whose email address is ``email``."""
        return DBSession.query(cls).filter_by(email=email).first()

    @classmethod
    def by_user_name(cls, username):
        """Return the user object whose user name is ``username``."""
        return DBSession.query(cls).filter_by(nombre_usuario=username).first()

    def _set_password(self, password):
        """Hash ``password`` on the fly and store its hashed version."""
        # Make sure password is a str because we cannot hash unicode objects
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        salt = sha1()
        salt.update(os.urandom(60))
        hash = sha1()
        hash.update(password + salt.hexdigest())
        password = salt.hexdigest() + hash.hexdigest()
        # Make sure the hashed password is a unicode object at the end of the
        # process because SQLAlchemy _wants_ unicode objects for Unicode cols
        if not isinstance(password, unicode):
            password = password.decode('utf-8')
        self._password = password

    def _get_password(self):
        """Return the hashed version of the password."""
        return self._password

    password = synonym('_password', descriptor=property(_get_password,
                                                        _set_password))

    #}

    def validate_password(self, password):
        """
        Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool

        """
        hash = sha1()
        if isinstance(password, unicode):
            password = password.encode('utf-8')
        hash.update(password + str(self.password[:40]))
        return self.password[40:] == hash.hexdigest()



class Permission(DeclarativeBase):
    """
    Permission definition for :mod:`repoze.what`.

    Only the ``permission_name`` column is required by :mod:`repoze.what`.

    """

    __tablename__ = 'tg_permission'

    #{ Columns

    permission_id = Column(Integer, autoincrement=True, primary_key=True)

    permission_name = Column(Unicode(63), unique=True, nullable=False)

    description = Column(Unicode(255))

    #{ Relations

    groups = relation(Group, secondary=group_permission_table,
                      backref='permissions')

    #{ Special methods

    def __repr__(self):
        return ('<Permission: name=%r>' % self.permission_name).encode('utf-8')

    def __unicode__(self):
        return self.permission_name

    #}


#}
