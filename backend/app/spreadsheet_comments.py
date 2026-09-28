"""Literal legacy notes and note-only VML; no author authentication or rendering."""
from .spreadsheet_parser import S, R, coordinate, column, reject

T = '{'+S+'}'
V = '{urn:schemas-microsoft-com:vml}'
O = '{urn:schemas-microsoft-com:office:office}'
X = '{urn:schemas-microsoft-com:office:excel}'


def literal(node):
    return {'tag': node.tag, 'attributes': dict(node.attrib), 'text': node.text or '',
            'tail': node.tail or '', 'children': [literal(c) for c in node]}


def comments(sheet, part, roots, relationships, seen):
    if any('threadedcomment' in kind.lower() or kind.endswith('/person') for kind,_ in relationships.values()):
        reject('threaded_comments_require_review', part)
    paths = [p for kind,p in relationships.values() if kind == R+'/comments']
    if len(paths)>1:
        reject('ambiguous_comment_part', part)
    notes=[]
    if paths:
        path=paths[0]
        if path in seen:reject('duplicate_comment_binding',path)
        seen.add(path);root=roots.get(path)
        if root is None or root.tag!=T+'comments' or [n.tag for n in root]!=[T+'authors',T+'commentList']:
            reject('unsupported_comment_structure',path)
        authors=[]
        for a in root[0]:
            if a.tag!=T+'author' or len(a):reject('unsupported_comment_author',path)
            authors.append(a.text or '')
        refs=set()
        rich={T+'text':{T+'t',T+'r'},T+'r':{T+'rPr',T+'t'},
              T+'rPr':{T+x for x in ('rFont','charset','family','b','i','strike','outline','shadow','condense','extend','color','sz','u','vertAlign','scheme')}}
        def check(n):
            if any(c.tag not in rich.get(n.tag,set()) for c in n):reject('unsupported_comment_rich_text',path)
            for c in n:check(c)
        for i,n in enumerate(root[1]):
            ref=n.get('ref','');coordinate(ref)
            aid=n.get('authorId','')
            if (n.tag!=T+'comment' or ref in refs or not aid.isdigit() or int(aid)>=len(authors)
                    or [c.tag for c in n]!=[T+'text']):reject('invalid_comment_identity_or_content',path,ref)
            if len(notes)>=10000:reject('comment_count_limit',path)
            refs.add(ref);text=n[0];check(text)
            notes.append({'cell':ref,'author_id':int(aid),'author':authors[int(aid)],
                'text':''.join(t.text or '' for t in text.iter(T+'t')),'attributes':dict(n.attrib),
                'rich_text':literal(text),'source_part':path,'source_xml_path':f'/comments/commentList/comment[{i+1}]',
                'author_verified':False,'professional_review':'unreviewed'})
    vml_links={rid:p for rid,(kind,p) in relationships.items() if kind==R+'/vmlDrawing'}
    bindings=sheet.findall(T+'legacyDrawing')
    if len(bindings)>1:reject('ambiguous_note_drawing_requires_review',part)
    if not bindings:
        if vml_links:reject('unbound_note_drawing',part)
        return notes,None
    binding=bindings[0];path=vml_links.get(binding.get('{'+R+'}id'))
    if len(binding) or not path or len(vml_links)!=1 or path in seen:reject('ambiguous_note_drawing_requires_review',part)
    seen.add(path);root=roots.get(path)
    if root is None or root.tag!='xml':reject('unsupported_note_drawing',path)
    allowed={
        'xml':{O+'shapelayout',V+'shapetype',V+'shape'},O+'shapelayout':{O+'idmap'},
        V+'shapetype':{V+'stroke',V+'path'},
        V+'shape':{V+'fill',V+'shadow',V+'path',V+'stroke',V+'textbox',X+'ClientData'},
        V+'textbox':{'div'},'div':set(),
        X+'ClientData':{X+x for x in ('MoveWithCells','SizeWithCells','Anchor','AutoFill','Row','Column','Visible','Locked','LockText','TextHAlign','TextVAlign')},
    }
    for n in root.iter():
        if any(c.tag not in allowed.get(n.tag,set()) for c in n):reject('non_note_drawing_requires_review',path)
        if any(k.rsplit('}',1)[-1].lower() in {'href','src','onload','onclick'} for k in n.attrib):
            reject('active_note_drawing',path)
    shape_refs=set();shape_ids=set()
    for shape in root.findall(V+'shape'):
        sid=shape.get('id')
        data=shape.findall(X+'ClientData')
        if not sid or sid in shape_ids or len(data)!=1 or data[0].get('ObjectType')!='Note':
            reject('non_note_drawing_requires_review',path)
        shape_ids.add(sid);d=data[0]
        if len([c.tag for c in d])!=len({c.tag for c in d}):reject('ambiguous_note_anchor',path)
        row=d.find(X+'Row');col=d.find(X+'Column')
        if row is None or col is None or not (row.text or '').isdigit() or not (col.text or '').isdigit():
            reject('invalid_note_anchor',path)
        rn,cn=int(row.text),int(col.text)
        if rn>=1048576 or cn>=16384:reject('invalid_note_anchor',path)
        ref=column(cn+1)+str(rn+1)
        if ref in shape_refs:reject('ambiguous_note_anchor',path,ref)
        shape_refs.add(ref)
    if shape_refs!={n['cell'] for n in notes}:reject('note_anchor_comment_mismatch',path)
    return notes,{'source_part':path,'declaration':literal(root),'note_cells':sorted(shape_refs),
                  'rendered':False,'visual_layout_verified':False}
