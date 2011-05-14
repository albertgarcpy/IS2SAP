# -*- coding: utf-8 -*-
"""Setup the IS2SAP application"""

import logging
from tg import config
from is2sap import model

import transaction


def bootstrap(command, conf, vars):
    """Place any commands to setup is2sap here"""

    # <websetup.bootstrap.before.auth
    from sqlalchemy.exc import IntegrityError
    try:
        u = model.Usuario()
        u.nombre = u'Raul Alberto'
        u.apellido = u'Benitez Martinez'
        u.nombre_usuario = u'raul'
        u.email = u'raul_kvd@hotmail.com'
        u.password = u'raul'
        u.direccion = u'Espanha c/ 10 de Agosto'
        u.telefono = u'021-574543'
        model.DBSession.add(u)

        v = model.Usuario()
        v.nombre = u'Elias Rene'
        v.apellido = u'Benitez Martinez'
        v.nombre_usuario = u'elias'
        v.email = u'elias_rene@hotmail.com'
        v.password = u'elias'
        v.direccion = u'Espanha c/ 10 de Agosto'
        v.telefono = u'021-574543'
        model.DBSession.add(v)
    
        g = model.Rol()
        g.nombre_rol = u'administrador'
        g.descripcion = u'Grupo Administrador'
        g.usuarios.append(u)
        model.DBSession.add(g)
    
        h = model.Rol()
        h.nombre_rol = u'editor'
        h.descripcion = u'Grupo Edicion'
        h.usuarios.append(v)
        model.DBSession.add(h)

        p = model.Permiso()
        p.nombre_permiso = u'administracion'
        p.descripcion = u'Este permiso dara un derecho administrativo al portador'
        p.roles.append(g)
        model.DBSession.add(p)

        q = model.Permiso()
        q.nombre_permiso = u'edicion'
        q.descripcion = u'Este permiso dara un derecho de edicion al portador'
        q.roles.append(h)
        model.DBSession.add(q)

        ef = model.EstadoFase()
        ef.nombre_estado = 'Inicial'
        model.DBSession.add(ef)

        ef = model.EstadoFase()
        ef.nombre_estado = 'Desarrollo'
        model.DBSession.add(ef)

        ef = model.EstadoFase()
        ef.nombre_estado = 'Con Linea Base Parciales'
        model.DBSession.add(ef)

        ef = model.EstadoFase()
        ef.nombre_estado = 'Con Lineas Bases'
        model.DBSession.add(ef)

        ef = model.EstadoFase()
        ef.nombre_estado = 'Finalizado'
        model.DBSession.add(ef)
    
        model.DBSession.flush()
        transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'
        

    # <websetup.bootstrap.after.auth>
