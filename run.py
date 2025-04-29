from app import app

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Comment': Comment}

if __name__ == '__main__':
    app.run()