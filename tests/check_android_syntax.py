"""Syntax-only validation; this is NOT an Android compile or device test."""
from pathlib import Path
from tree_sitter import Language,Parser
import tree_sitter_java,json
parser=Parser(Language(tree_sitter_java.language()));result=[]
for path in Path('android/app/src/main/java').rglob('*.java'):
    tree=parser.parse(path.read_bytes());errors=[]
    def visit(node):
        if node.type=='ERROR' or node.is_missing:errors.append({'type':node.type,'line':node.start_point.row+1})
        for child in node.children:visit(child)
    visit(tree.root_node);result.append({'file':str(path),'errors':errors})
print(json.dumps(result,indent=2));assert not any(r['errors'] for r in result)
