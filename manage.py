import click
from app import app, db
from app.models import Message, Friend, Claimant, Admin


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Message': Message, 'Friend': Friend,
            'Claimant': Claimant, 'Admin': Admin}


@click.group()
def cli():
    pass


@cli.command()
def run():
    from app import app
    host = app.config['HOST']
    port = app.config['PORT']

    # if __name__ != '__main__':
    #     gunicorn_logger = logging.getLogger('gunicorn.error')
    #     app.logger.handlers = gunicorn_logger.handlers
    #     app.logger.setLevel(gunicorn_logger.level)
    # else:

    app.run(host=host, port=port)
    print('ha')


if __name__ == '__main__':
    cli()
