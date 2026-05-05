import os
import shutil

def main():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(root_dir, 'frontend')
    backend_dir = os.path.join(root_dir, 'backend')

    print("Creating directories...")
    os.makedirs(frontend_dir, exist_ok=True)
    os.makedirs(backend_dir, exist_ok=True)

    # 1. Move Frontend Files
    frontend_items = ['static', 'templates', 'analyze.html']
    for item in frontend_items:
        src = os.path.join(root_dir, item)
        dst = os.path.join(frontend_dir, item)
        if os.path.exists(src):
            print(f"Moving {item} to frontend/")
            shutil.move(src, dst)

    # 2. Update app.py before moving it
    app_py_path = os.path.join(root_dir, 'app.py')
    if os.path.exists(app_py_path):
        print("Updating app.py paths...")
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace Flask instantiation
        old_flask = 'app = Flask(__name__)'
        new_flask = '''
# Configure paths for the new backend/frontend structure
basedir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.join(os.path.dirname(basedir), 'frontend')

app = Flask(__name__, 
            template_folder=os.path.join(frontend_dir, 'templates'),
            static_folder=os.path.join(frontend_dir, 'static'))
'''
        content = content.replace(old_flask, new_flask.strip())

        # Replace upload config
        old_upload = 'app.config["UPLOAD_FOLDER"] = "uploads"'
        new_upload = 'app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "uploads")'
        content = content.replace(old_upload, new_upload)

        # Replace DB config
        old_db = "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'"
        new_db = "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')"
        content = content.replace(old_db, new_db)

        # Write the updated content
        with open(app_py_path, 'w', encoding='utf-8') as f:
            f.write(content)

    # 3. Move Backend Files
    backend_items = ['app.py', 'analyzer.py', 'database.db', 'resumecheck.db', 'requirements.txt', 'instance', 'uploads']
    for item in backend_items:
        src = os.path.join(root_dir, item)
        dst = os.path.join(backend_dir, item)
        if os.path.exists(src):
            print(f"Moving {item} to backend/")
            try:
                shutil.move(src, dst)
            except PermissionError:
                print(f"ERROR: Cannot move {item}. Make sure the Flask server is stopped!")
                return

    print("Project successfully restructured!")
    print("To run your app, cd into 'backend' and run 'python app.py'")

if __name__ == '__main__':
    main()
