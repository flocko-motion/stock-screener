
class Col:
    def __init__(self, field: str, title: str):
        self.field = field
        self.title = title

def to_table(data, cols):
    table = {
        "cols": cols,
        "rows": []
    }

    for item in data:
        row = [item.get(col.field, None) for col in cols]
        table["rows"].append(row)

    return table
