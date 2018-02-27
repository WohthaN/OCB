# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

import odoo.tests

RE_ONLY = re.compile('QUnit\.only\(')


class WebSuite(odoo.tests.HttpCase):
    post_install = True
    at_install = False

    def test_01_js(self):
        # webclient desktop test suite
        self.phantom_js('/web/tests?mod=web', "", "", login='admin', timeout=360)

    def test_02_js(self):
        # webclient mobile test suite
        self.phantom_js('/web/tests/mobile?mod=web', "", "", login='admin', timeout=300)

    def test_check_suite(self):
        # verify no js test is using `QUnit.only` as it forbid any other test to be executed
        self._check_only_call('web.qunit_suite')
        self._check_only_call('web.qunit_mobile_suite')

    def _check_only_call(self, suite):
        # As we currently aren't in a request context, we can't render `web.layout`.
        # redefinied it as a minimal proxy template. To avoid reference errors, any template
        # depending on it is minimized as well.

        minimal_template = """
        <t t-name="web.layout">
            <t t-raw="head"/>
        </t>
        """
        View_model = self.env['ir.ui.view']

        web_layout_view = self.env.ref('web.layout')

        inheriting_views = web_layout_view.get_inheriting_views_arch(web_layout_view.ids[0], None)
        inheriting_views = [x[1] for x in
                            inheriting_views]  # get_inheriting_views_arch returns ["view content", view_id)]

        for view_id in inheriting_views:
            view = View_model.browse(view_id)
            view.write({'arch_db': minimal_template})

        web_layout_view.write({'arch_db': minimal_template})

        for asset in self.env['ir.qweb']._get_asset_content(suite, options={})[0]:
            filename = asset['filename']
            if not filename or asset['atype'] != 'text/javascript':
                continue
            with open(filename, 'r') as fp:
                if RE_ONLY.search(fp.read()):
                    self.fail("`QUnit.only()` used in file %r" % asset['url'])
