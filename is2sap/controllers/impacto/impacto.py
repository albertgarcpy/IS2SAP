# -*- coding: utf-8 -*-
"""Controlador de Relacion"""

class Impacto:
    def __init__(self):
        self.itemsAfectados=[]
        self.listaRelaciones = []

    def buscarRelaciones(self, itemActual):
        # En esta busqueda yo busco todos los que son hijos del item actual que esta revisando
        hijos = DBSession.query(RelacionItem).filter_by(id_item1=idItemActual).filter_by(tipo="Padre-Hijo").order_by(RelacionItem.id_item2).all()
        for hijo in hijos:
            relacion = (hijo.id_item1, hijo.id_item2)
            if self.listaRelaciones.count(relacion) == 0:
                self.listaRelaciones.append(relacion)
            if self.itemsAfectados.count(hijo.id_item2) == 0:
                self.itemsAfectados.append(hijo.id_item2)

        # Esto busca los padres del item actual que esta revisando
        padres = DBSession.query(RelacionItem).filter_by(id_item2=idItemActual).filter_by(tipo="Padre-Hijo").order_by(RelacionItem.id_item1).all()
        for padre in padres:
            relacion = (padre.id_item1, padre.id_item2)
            if self.listaRelaciones.count(relacion) == 0:
                self.listaRelaciones.append(relacion)
            if self.itemsAfectados.count(padre.id_item1) == 0:
                self.itemsAfectados.append(padre.id_item1)

        # Esto busca los antecesores del item actual que se esta revisando
        antecesores = DBSession.query(RelacionItem).filter_by(id_item2=idItemActual).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item1).all()
        for antecesor in antecesores:
            relacion = (antecesor.id_item1, antecesor.id_item2)
            if self.listaRelaciones.count(relacion) == 0:
                self.listaRelaciones.append(relacion)
            if self.itemsAfectados.count(antecesor.id_item1) == 0:
                self.itemsAfectados.append(antecesor.id_item1)

        # Esto busca los sucesores del item actual que se esta revisando
        sucesores = DBSession.query(RelacionItem).filter_by(id_item1=idItemActual).filter_by(tipo="Antecesor-Sucesor").order_by(RelacionItem.id_item2).all()
        for sucesor in sucesores:
            relacion = (sucesor.id_item1, sucesor.id_item2)
            if self.listaRelaciones.count(relacion) == 0:
                self.listaRelaciones.append(relacion)
            if self.itemsAfectados.count(sucesor.id_item2) == 0:
                self.itemsAfectados.append(sucesor.id_item2)


    def calcularImpacto(self, id_proyecto, itemActual):
        itemsAfectados.append(itemActual) # este realiza la primera insercion del item para el cual se quiere calcular el impacto
        impactoTotal=0
        for item in itemsAfectados:
            buscarRelaciones(item)
        ## traer las fases del proyecto y luego los items de las fases, sumar por fases, y luego un total
        proyecto = DBSession.query(Proyecto).get(id_proyecto)
        print "El proyecto es :", proyecto.nombre
        for fase in proyecto.fases:
            itemsDeFase = DBSession.query(Item).join(TipoItem).join(Fase).filter(Fase.id_fase==fase.id_fase).all()
            impactoPorFase=0
            for item in itemsDeFase:
                if itemsAfectados.count(item.id_item) == 1:
                    impactoPorFase = impactoPorFase + int(item.complejidad)
            impactoTotal = impactoTotal + impactoPorFase
            print "El impacto de la "+fase.nombre+" es :", impactoPorFase
        print "El impacto total es :", impactoTotal

if __name__ == '__main__':
    calcular = Impacto()
    calcular.cacularImpacto(1, 6)
