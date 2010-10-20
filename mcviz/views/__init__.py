from views import GraphView
from tools import contract_jets, remove_kinks, gluballs, chainmail, contract_loops, pluck, unsummarize
from tagging import tag

view_tools = {}
view_tools["kinks"] = remove_kinks
view_tools["gluballs"] = gluballs
view_tools["chainmail"] = chainmail
view_tools["jets"] = contract_jets
view_tools["loops"] = contract_loops
view_tools["pluck"] = pluck
view_tools["unsummarize"] = unsummarize

def list_view_tools():
    return sorted(view_tools.keys())

def apply_view_tool(name, graph_view):
    view_tools[name](graph_view)