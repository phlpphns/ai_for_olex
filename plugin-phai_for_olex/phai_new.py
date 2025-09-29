from olexFunctions import OlexFunctions

OV = OlexFunctions()

import os
import htmlTools
import olex
import olx
import gui
import time

debug = bool(OV.GetParam("olex2.debug", False))


instance_path = OV.DataDir()

try:
    from_outside = False
    p_path = os.path.dirname(os.path.abspath(__file__))
except:
    from_outside = True
    p_path = os.path.dirname(os.path.abspath("__file__"))

l = open(os.sep.join([p_path, "def.txt"])).readlines()
d = {}
for line in l:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    d[line.split("=")[0].strip()] = line.split("=")[1].strip()

p_name = d["p_name"]
p_htm = d["p_htm"]
p_img = eval(d["p_img"])
p_scope = d["p_scope"]

OV.SetVar("phai_new_plugin_path", p_path)

from PluginTools import PluginTools as PT

# from PluginLib.plugin-phai_new.PhAI_for_olex2 import _create_solution_map
from PhAI_for_olex2 import create_solution_map


class phai_new(PT):
    def __init__(self):
        super(phai_new, self).__init__()
        self.p_name = p_name
        self.p_path = p_path
        self.p_scope = p_scope
        self.p_htm = p_htm
        self.p_img = p_img
        self.deal_with_phil(operation="read")
        self.print_version_date()
        if not from_outside:
            self.setup_gui()
        OV.registerFunction(self.print_formula, True, "phai_new")
        OV.registerFunction(self.create_solution_map, True, "phai_new")
        OV.registerFunction(self.solve, True, "phai_new")
        OV.registerFunction(self.print_hkl_info, False, "phai_new")
        OV.registerFunction(self.get_cycles, False, "phai_new")
        OV.registerFunction(self.get_versions_phai, False, "phai_new")
        OV.registerFunction(self.set_id, False, "phai_new")
        OV.registerFunction(self.list_versions, False, "phai_new")
        OV.registerFunction(self.init_plugin, False, "phai_new")


        # END Generated =======================================

    def create_solution_map(self, cycles=5, max_peaks="auto"):
        print("BANANA")
        create_solution_map(cycles, max_peaks)
        print("Apple")

    def solve(self, cycles=5, max_peaks="auto"):
        olex.m('fuse')
        olex.m('reset')
        self.create_solution_map(cycles, max_peaks)
        olex.m('sel $Q')
        olex.m('name C')
        #olex.m('ata')

        for i in range(3):
            olex.m("ata(1)")
            olex.m("refine 4")
            olex.m("ata(1)")
            olex.m("compaq")
            olex.m("grow")
            olex.m("anis")
            olex.m("refine 4")

    def print_formula(self):
        formula = {}
        for element in str(olx.xf.GetFormula("list")).split(","):
            element_type, n = element.split(":")
            print("%s: %s" % (element_type, n))
            formula.setdefault(element_type, float(n))

    def print_hkl_info(self):
        self.hklfile = OV.HKLSrc().rsplit("\\", 1)[-1].rstrip(".hkl")
        print(self.hklfile)
        filename = self.hklfile + ".hkl"
        print(filename)
        print(os.path.abspath(filename))
        hkl_file_old = list(olex_hkl.Read(filename))
        [print(line) for line in hkl_file_old]
        # if not filename:
        # if not new_file:
        #   new_file=self.hklfile+'twinX.hkl'
        # metrical=self.getMetrical()
        # metrical_inv=numpy.linalg.inv(metrical)
        # twin_law=twin_law_full.hkl_rotation
        print("\n\n\n\n")

    def get_cycles(self):
        cycles = OV.GetParam("phai_new.variables.cycles")
        # if int(cycles) < 1:
        #     fvar = -(float(abs(var)) * 10 + float(occ))
        # else:
        #     fvar = float(var) * 10 + float(occ)
        # olx.html.SetValue("FVAROCC", cycles)
        # OV.SetParam("phai_new.variables.fvarocc", fvar)
        return cycles

    def get_versions_phai(self):
        versions = ['PhAI_P21_c']
        # db = FragmentTable(self.dbfile, self.userdbfile)
        # items = ";".join(["{}<-{}".format(i[1], i[0]) for i in db])
        return versions

    def set_id(self, fragid=0):
        """
        Sets the fragment id in the phil for the search field
        """
        try:
          int(fragid)
        except(ValueError):
          return False
        # print('### Selected fragment {}'.format(fragid))
        OV.SetParam("phai_new.variables.version_phai", version_phai)
        self.version_phai = int(version_phai)
        return True

    def list_versions(self):
      """
      returns the available fragments in the database
      the list of names is separated by semicolon
      i[0] => number
      i[1] => name
      """
      # db = FragmentTable(self.dbfile, self.userdbfile)
      # items = ';'.join(['{}<-{}'.format(i[1], i[0]) for i in db])
      items = self.get_versions_phai()
      olx.html.SetItems('LIST_PHAI_VERSIONS', items)

    def init_plugin(self):
      """
      initialize the plugins main form
      """
      # self.get_resi_class()
      # self.set_fragment_picture()
      # self.display_image('FDBMOLEPIC', 'displayimg.png')
      # self.show_reference()
      # resinum = self.find_free_residue_num()
      # olx.html.SetValue('RESIDUE', True)
      # OV.SetParam('FragmentDB.fragment.resinum', resinum)
      # #self.list_all_fragments()

      OV.SetParam('phai_new.variables.name_phai', self.get_versions_phai()[0])
      olx.html.SetValue('LIST_PHAI_VERSIONS', self.list_versions() )# OV.GetParam('FragmentDB.new_fragment.frag_name'))




phai_new_instance = phai_new()
print("OK.")
