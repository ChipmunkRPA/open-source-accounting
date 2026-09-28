"""Literal SpreadsheetML table declarations; never evaluate filters or formulas."""
from .spreadsheet_parser import S, R, coordinate, reject

T = '{' + S + '}'


def rectangle(value, part):
    refs = value.split(':')
    if len(refs) == 1:
        refs *= 2
    if len(refs) != 2:
        reject('invalid_table_range', part)
    a, b = map(coordinate, refs)
    if a[0] > b[0] or a[1] > b[1]:
        reject('invalid_table_range', part)
    return a, b


def declaration(root, part):
    if root is None or root.tag != T+'table':
        reject('invalid_table_part', part)
    a, b = rectangle(root.get('ref', ''), part)
    if not root.get('id', '').isdigit() or int(root.get('id')) < 1 or not root.get('displayName') or not root.get('name'):
        reject('invalid_table_identity', part)
    for key in ('headerRowCount', 'totalsRowCount'):
        if root.get(key, '1' if key == 'headerRowCount' else '0') not in {'0', '1'}:
            reject('unsupported_table_row_counts', part)
    if int(root.get('headerRowCount', '1')) + int(root.get('totalsRowCount', '0')) > b[0]-a[0]+1:
        reject('invalid_table_row_counts', part)
    if root.get('tableType', 'worksheet') != 'worksheet':
        reject('external_table_requires_review', part)
    allowed = {
        'table': {'autoFilter', 'sortState', 'tableColumns', 'tableStyleInfo'},
        'tableColumns': {'tableColumn'},
        'tableColumn': {'calculatedColumnFormula', 'totalsRowFormula'},
        'autoFilter': {'filterColumn', 'sortState'},
        'filterColumn': {'filters', 'customFilters', 'dynamicFilter', 'colorFilter', 'iconFilter', 'top10'},
        'filters': {'filter', 'dateGroupItem'}, 'customFilters': {'customFilter'},
        'sortState': {'sortCondition'},
    }
    def node(n):
        if not n.tag.startswith(T):
            reject('unsupported_table_namespace', part)
        tag = n.tag[len(T):]
        for child in n:
            if child.tag not in {T+x for x in allowed.get(tag, set())}:
                reject('unsupported_table_content_requires_review', part)
        tags = [c.tag for c in n]
        if tag in {'table', 'tableColumn', 'filterColumn'} and len(tags) != len(set(tags)):
            reject('ambiguous_table_content', part)
        return {'element': tag, 'attributes': dict(n.attrib), 'text': n.text or '', 'children': [node(c) for c in n]}
    literal = node(root)
    cols = root.find(T+'tableColumns')
    if cols is None or cols.get('count') != str(len(cols)) or len(cols) != b[1]-a[1]+1:
        reject('table_column_count_mismatch', part)
    ids, names = set(), set()
    columns = []
    for i, col in enumerate(cols):
        cid, name = col.get('id', ''), col.get('name', '')
        if not cid.isdigit() or int(cid) < 1 or int(cid) in ids or not name or name.casefold() in names:
            reject('ambiguous_table_column', part)
        ids.add(int(cid)); names.add(name.casefold())
        columns.append({'worksheet_column': a[1]+i, **node(col)})
    filt = root.find(T+'autoFilter')
    if filt is not None:
        fa, fb = rectangle(filt.get('ref', ''), part)
        if fa[0] < a[0] or fa[1] != a[1] or fb[0] > b[0] or fb[1] != b[1]:
            reject('table_filter_range_mismatch', part)
        seen = set()
        for f in filt.findall(T+'filterColumn'):
            colid = f.get('colId', '')
            if not colid.isdigit() or int(colid) >= len(cols) or int(colid) in seen:
                reject('invalid_table_filter_column', part)
            seen.add(int(colid))
    return {'source_part': part, 'id': str(int(root.get('id'))), 'name': root.get('name'),
            'display_name': root.get('displayName'), 'range': root.get('ref'),
            'start': list(a), 'end': list(b), 'columns': columns,
            'declaration': literal, 'filters_applied': False, 'formulas_calculated': False,
            'header_values_verified': False}


def tables(sheet, part, roots, relationships, seen_parts, identities, defined_names):
    containers = sheet.findall(T+'tableParts')
    if len(containers) > 1:
        reject('ambiguous_table_bindings', part)
    links = {rid: path for rid, (kind, path) in relationships.items() if kind == R+'/table'}
    if not containers:
        if links:
            reject('unbound_table_relationship', part)
        return []
    container = containers[0]
    if container.get('count') != str(len(container)) or not len(container):
        reject('table_parts_count_requires_review', part)
    result, used = [], set()
    for binding in container:
        rid = binding.get('{'+R+'}id')
        target = links.get(rid)
        if binding.tag != T+'tablePart' or len(binding) or not target or rid in used or target in seen_parts:
            reject('ambiguous_table_binding', part)
        used.add(rid); seen_parts.add(target)
        if len(seen_parts) > 100:
            reject('table_count_limit', part)
        table = declaration(roots.get(target), target)
        keys = [('id', table['id']), ('name', table['name'].casefold()), ('display', table['display_name'].casefold())]
        if any(k in identities for k in keys) or table['display_name'].casefold() in defined_names:
            reject('duplicate_table_identity', target)
        identities.update(keys)
        a, b = table['start'], table['end']
        for prior in result:
            c, d = prior['start'], prior['end']
            if a[0] <= d[0] and c[0] <= b[0] and a[1] <= d[1] and c[1] <= b[1]:
                reject('overlapping_table_ranges', target)
        result.append(table)
    if used != set(links):
        reject('unbound_table_relationship', part)
    return result
