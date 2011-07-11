# -*- coding: utf-8 -*-
"""Clase que implementa un test para el modulo de Configuracion"""
import unittest
from is2sap import *
import transaction
from tg import config
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DataError
from is2sap.lib.base import BaseController
from sqlalchemy import *
from sqlalchemy.orm import mapper, relation, backref, synonym, sessionmaker
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, synonym
#from is2sap.model import DeclarativeBase, metadata, DBSession
from is2sap.model.model import TipoItem, Item, Proyecto, Usuario, Fase, LineaBase
from is2sap.tests import setup_db, teardown_db
from is2sap.controllers.linea_base_controlador import LineaBaseController


class DesarrolloTest(unittest.TestCase):
    """Unidad de prueba para el modulo de Configuracion"""

    def setUp(self):
        """Metodo llamado antes de ejecutar el test"""
	db = create_engine('postgresql://postgres:postgres@localhost:5432/IS2SAP_DB')
	Session = sessionmaker(bind=db)
	self.DBSession = Session()
        self.proyecto = Proyecto()
        self.proyecto.id_usuario="1"
        self.proyecto.nombre = "Proyecto de prueba"
        self.proyecto.descripcion = "Este es un proyecto de prueba"
        self.proyecto.fecha = "11/07/2011"
        self.proyecto.iniciado = False
        self.DBSession.add(self.proyecto)
        self.DBSession.flush()
        transaction.commit()

        self.fase = Fase()
        self.fase.id_estado_fase="1"
        self.fase.id_proyecto = self.proyecto.id_proyecto
        self.fase.nombre = "Fase1 del PP"
        self.fase.descripcion = "Esta es la primera fase del Proyecto de prueba"
        self.fase.numero_fase = "1"
        self.DBSession.add(self.fase)
        self.DBSession.flush()
        transaction.commit()

        self.tipo_item = TipoItem()
        self.tipo_item.id_fase = self.fase.id_fase
        self.tipo_item.nombre = "Tipo Item1 del Proyecto de Prueba"
        self.tipo_item.codigo = "TIP"
        self.tipo_item.descripcion = "Este tipo de item es de prueba"
        self.DBSession.add(self.tipo_item)
        self.DBSession.flush()
        transaction.commit()

        self.item = Item()
        self.item.id_tipo_item = self.tipo_item.id_tipo_item
        self.item.codigo = self.tipo_item.codigo
        self.item.descripcion = "Item creado para prueba"
        self.item.complejidad = "5"
        self.item.prioridad = "Baja"
        self.item.estado = "Desarrollo"
        self.item.version = "1"
        self.item.observacion = "Obs"
        self.item.fecha_modificacion = "11/07/2011"
        self.item.vivo = True
        self.DBSession.add(self.item)
        self.DBSession.flush()
        transaction.commit()

        self.linea_base = LineaBase()
	self.linea_base.nombre = "Linea Base de Prueba"
        self.linea_base.descripcion = "Esta linea base es para prueba"
        self.linea_base.estado = 1
        self.linea_base.id_fase = self.fase.id_fase
        self.linea_base.version = "1"
        self.DBSession.add(self.linea_base)
        self.DBSession.flush()
        transaction.commit()
	
    def runTest(self):
        """Metodo llamado para ejecutar el test"""
	self.testCampoNombreLineaBase()

    def testCampoNombreLineaBase(self):
	"""Metodo que realiza el test. Comprueba que se genere un IntegrityError al introducir 
           un valor incorrecto para el campo Nombre de Linea Base
        """
        try:
           self.linea_base.nombre = None
           self.DBSession.flush()
        except IntegrityError:
           pass
        else:
           self.fail("Se esperaba un IntegrityError! Verificar...")

		
if __name__ == "__main__":
	unittest.main()
