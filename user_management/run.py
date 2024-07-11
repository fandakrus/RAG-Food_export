from app import create_app

app = create_app()

def list_routes(app):
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote(f"{rule.endpoint:50s} {methods:20s} {str(rule)}")
        output.append(line)
    
    for line in sorted(output):
        print(line)

if __name__ == '__main__':
    list_routes(app)
    app.run(debug=True)