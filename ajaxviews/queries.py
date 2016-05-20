from dateutil.parser import parse
from django.db.models import QuerySet


class AjaxQuerySet(QuerySet):
    """ define field type in views e.g. fk, m2m, set
        specify field name and it's path
    """
    distinct_qs = True

    def default_filter(self, opts, *args, **kwargs):
        return self.ajax_filter(opts, *args, **kwargs).ajax_sorter(opts)

    def ajax_filter(self, opts, *args, **kwargs):
        # args = set()
        # args.update((Q(field__isnull=True) | Q(field__name='none'),))
        filter_field = opts.get('filter_field', None)
        if isinstance(filter_field, tuple) and len(filter_field) == 2 and\
           (filter_field[1] == 'exclude' or filter_field[1] == 'exclude_filter'):
            return self.filter(*args, **kwargs)

        if opts.get('selected_filter_index', -1) >= 0 and opts.get('selected_filter_values', None):
            filter_field = opts['filter_field']
            if isinstance(filter_field, str):
                kwargs[filter_field + '__in'] = opts['selected_filter_values']
            elif isinstance(filter_field, tuple) and len(filter_field) == 3:
                kwargs[filter_field[0] + '__in'] = opts['selected_filter_values']
            elif isinstance(filter_field, tuple) and len(filter_field) == 2 and filter_field[1] == 'date':
                if opts['selected_filter_values'].get('min_date', None):
                    kwargs[filter_field[0] + '__gte'] = parse(opts['selected_filter_values']['min_date']).date()
                if opts['selected_filter_values'].get('max_date', None):
                    kwargs[filter_field[0] + '__lte'] = parse(opts['selected_filter_values']['max_date']).date()
            else:
                raise Exception('Misconfigured filter fields!')

        if self.distinct_qs:
            return self.filter(*args, **kwargs).distinct()
        return self.filter(*args, **kwargs)

    def ajax_sorter(self, opts):
        if opts.get('sort_index', -1) < 0:
            return self
        sort_field = opts['sort_field']
        if isinstance(sort_field, tuple) and len(sort_field) == 2 and\
           (sort_field[1] == 'exclude' or sort_field[1] == 'exclude_sort'):
            return self
        field = sort_field if isinstance(sort_field, str) else sort_field[0]
        if opts.get('sort_order', '') == 'asc':
            return self.order_by(field)
        return self.order_by('-' + field)

    def get_unique_values(self, field):
        return self.order_by(field).distinct(field).values_list(field, flat=True)
