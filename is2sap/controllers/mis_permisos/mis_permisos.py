from repoze.what.predicates import Predicate

class permiso_en_fase(Predicate):

    message = 'No puede realizar la accion en esta fase!'

    def __init__(self, permiso, dic_fases_permisos, **kwargs):
        self.permiso = permiso
        self.dic_fases_permisos = dic_fases_permisos
        super(permiso_en_fase, self).__init__(**kwargs)

    def evaluate(self, environ, credentials):
        if self.dic_fases_permisos.count(self.permiso) == 0:
            self.unmet()
