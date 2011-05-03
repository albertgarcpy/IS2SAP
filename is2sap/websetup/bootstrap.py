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
        u.nombre_usuario = u'admin'
        u.email = u'raul_kvd@hotmail.com'
        u.password = u'admin'
        u.direccion = u'Espanha c/ 10 de Agosto'
        u.telefono = u'021-574543'
        model.DBSession.add(u)

        v = model.Usuario()
        v.nombre = u'Elias Rene'
        v.apellido = u'Benitez Martinez'
        v.nombre_usuario = u'editor'
        v.email = u'elias_rene@hotmail.com'
        v.password = u'editor'
        v.direccion = u'Espanha c/ 10 de Agosto'
        v.telefono = u'021-574543'
        model.DBSession.add(v)
    
        g = model.Group()
        g.group_name = u'managers'
        g.display_name = u'Grupo Administrador'
        g.users.append(u)
        model.DBSession.add(g)
    
#        h = model.Group()
#        h.group_name = u'managers'
#        h.display_name = u'Grupo Managers'
#        h.users.append(u)
#        model.DBSession.add(h)

        p = model.Permission()
        p.permission_name = u'administrador'
        p.description = u'Este permiso dara un derecho administrativo al portador'
        p.groups.append(g)
#        p.groups.append(h)
        model.DBSession.add(p)
    
        model.DBSession.flush()
        transaction.commit()
    except IntegrityError:
        print 'Warning, there was a problem adding your auth data, it may have already been added:'
        import traceback
        print traceback.format_exc()
        transaction.abort()
        print 'Continuing with bootstrapping...'
        

    # <websetup.bootstrap.after.auth>
