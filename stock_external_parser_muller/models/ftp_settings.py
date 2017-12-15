from openerp import (
    models,
    fields,
    api
)


# -----------------------------------------------------------------------
# STATES DICTIONARY
# TODO: these should go in generic parser
PARSER_STATE_NEW = "Inactive"
PARSER_STATE_RUNNING = "Confirmed"


class MullerParser(models.Model):
    # parent generic parser
    _inherit = ['kliemo_orders_parser.ftpsettings']

    @api.model
    def _type_selection(self):
        selection = super(MullerParser, self)._type_selection()
        selection.append(('muller', 'Muller Verlag'))
        return selection

    type = fields.Selection(_type_selection, string='Type', required=True)
    report_to_email = fields.Char(String="Report to Email", required=True, states={PARSER_STATE_NEW: [('readonly', False)],}, readonly=True)
