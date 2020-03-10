import unittest
from app import app, db
from app.models import Message, Link, Admin
from collections import namedtuple
from app.routes import make_cmd, healthcheck  # test_cmd


class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()
        a = Admin(name='test_admin', chat_id=0)
        db.session.add(a)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_linking(self):
        message = Message(tlg_chat_id=1,
                          tlg_msg_id=1,
                          text='test',
                          media_group_id=None,
                          from_user=1,
                          to_user=2,
                          file_ids=[],
                          from_claimant=True)

        db.session.add(message)
        db.session.commit()

        b_m = namedtuple('b_m', ['message_id'])
        bot_message = b_m(message_id=2)

        link = Link(from_chat_id=message.tlg_chat_id,
                    source_message_id=message.tlg_msg_id,
                    current_message_id=bot_message.message_id,
                    claimant='test_claimant')

        db.session.add(link)
        db.session.commit()

        cl_chat_id_raw = Link.query\
            .filter_by(current_message_id=bot_message.message_id)\
            .first()

        old_message = Message.query\
            .filter_by(tlg_chat_id=cl_chat_id_raw.source_message_id).first()

        self.assertEqual(old_message, message)

    def test_save_link(self):
        link = Link(from_chat_id=3,
                    source_message_id=2,
                    current_message_id=3,
                    claimant='test_claimant2')

        db.session.add(link)
        db.session.commit()

        cl_chat_id_raw = Link.query\
            .filter_by(current_message_id=3)\
            .first()

        self.assertEqual(cl_chat_id_raw, link)

    def test_make_cmd(self):
        # message = Message(tlg_chat_id=4,
        #                   tlg_msg_id=4,
        #                   text='test4',
        #                   media_group_id=None,
        #                   from_user=4,
        #                   to_user=2,
        #                   file_ids=[],
        #                   from_claimant=False)

        # db.session.add(message)
        # db.session.commit()

        resp = make_cmd(cmd='test_cmd')
        example = f'''all is good'''

        self.assertEqual(resp, example)

    def test_healthcheck(self):
        resp = healthcheck()
        self.assertEqual(resp, 'ok')


if __name__ == '__main__':
    unittest.main(verbosity=2)
