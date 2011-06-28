import unittest

from is2sap import model 
import transaction
from tg import config
from sqlalchemy import *
from sqlalchemy.orm import mapper, relation, backref, synonym, sessionmaker
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, synonym
from is2sap.model import DeclarativeBase, metadata, DBSession


#~ from sgs.config.enviroment import load_enviroment

class utilTestCase(unittest.TestCase):

	def setUp(self):
		#configuraciones para las pruebas
		# 
		#por ej. 
		#self.obj = Usuario()
		#
		#
		#conexion a BD
		db = create_engine('postgresql://postgres:postgres@localhost:5432/IS2SAP_DB')
		Session = sessionmaker(bind=db)
		self.session = Session()
		#self.un_proyecto = session.query(Proyecto).get(1)
	
	#este es el metodo que se ejecuta al darle desde la 
	#consola "python ejemplo_pyunit.py"
	#asi mismo se tiene que llamar runTest(self):
	def runTest(self):
		self.test_1()
		#self.test_2()
		#self.test_3()

	def test_1(self):
		"""Username de usuario es unico"""
		#~ 
		#~ No pueden existir dos usuario que posean los mismos users names
		#~ resultado = algun_proceso_de_tu_aplicacion()
		#~ assert valor_esperado == resultado, 'No son iguales'
		usuarios = self.session.query(model.Usuario).all()
		lista = []
		for usr in usuarios:
			lista.append(usr.nombre_usuario)
		
		assert len(lista) == len(set(lista)), 'No son iguales'
		
		

if __name__ == "__main__":
	unittest.main()
