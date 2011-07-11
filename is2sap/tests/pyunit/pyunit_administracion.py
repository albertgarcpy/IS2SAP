# -*- coding: utf-8 -*-
"""Clase que implementa un test para el modulo de Administracion"""
import unittest
from is2sap import *
import transaction
from tg import config
from sqlalchemy import *
from sqlalchemy.orm import mapper, relation, backref, synonym, sessionmaker
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, synonym
#from is2sap.model import DeclarativeBase, metadata, DBSession
from is2sap.model.model import TipoItem, Item, Proyecto, Fase, Usuario


class AdministracionTest(unittest.TestCase):
    """Unidad de prueba para el modulo de Administracion."""

    def setUp(self):
        """Metodo llamado antes de ejecutar el test"""
	db = create_engine('postgresql://postgres:postgres@localhost:5432/IS2SAP_DB')
	Session = sessionmaker(bind=db)
	DBSession = Session()
        self.proyecto = Proyecto()
        self.proyecto.id_usuario="1"
        self.proyecto.nombre = "Proyecto de prueba"
        self.proyecto.descripcion = "Este es un proyecto de prueba"
        self.proyecto.fecha = "11/07/2011"
        self.proyecto.iniciado = False
        DBSession.add(self.proyecto)
        DBSession.flush()
        transaction.commit()

        self.fase = Fase()
        self.fase.id_estado_fase="1"
        self.fase.id_proyecto = self.proyecto.id_proyecto
        self.fase.nombre = "Fase1 del PP"
        self.fase.descripcion = "Esta es la primera fase del Proyecto de prueba"
        self.fase.numero_fase = "1"
        DBSession.add(self.fase)
        DBSession.flush()
        transaction.commit()

        self.tipo_item = TipoItem()
        self.tipo_item.id_fase = self.fase.id_fase
        self.tipo_item.nombre = "Tipo Item1 del Proyecto de Prueba"
        self.tipo_item.codigo = "TIP"
        self.tipo_item.descripcion = "Este tipo de item es de prueba"
        DBSession.add(self.tipo_item)
        DBSession.flush()
        transaction.commit()

        self.usuarios = DBSession.query(Usuario).all()
	
    def runTest(self):
        """Metodo llamado para ejecutar el test"""
	self.testNombreUsuarioUnico()
        self.testCamposNoNulos()

    def testNombreUsuarioUnico(self):
	"""Metodo que realiza el test. Comprueba que todos los nombre de usuario sean unicos"""

	lista = []

	for usuario in self.usuarios:
	    lista.append(usuario.nombre_usuario)
		
	assert len(lista) == len(set(lista)), 'Hay nombres de usuario repetidos!'

    def testCamposNoNulos(self):
	"""Metodo que realiza el test. Comprueba campos no nulos de Proyecto, Fase
           y Tipo de Item
        """

	assert self.proyecto.nombre != "", 'Nombre de proyecto nulo!'
	assert self.fase.nombre != "", 'Nombre de fase nulo!'
        assert self.tipo_item.nombre != "", 'Nombre de tipo de item nulo!'
		
		
if __name__ == "__main__":
	unittest.main()
