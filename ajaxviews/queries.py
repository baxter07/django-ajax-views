from dateutil.parser import parse
from django.db.models import QuerySet


class AjaxQuerySet(QuerySet):
    """
    This QuerySet enhances generic filter options that work together with server side
    :class:`ajaxviews.views.AjaxListView` and client side :class:`FilterView`. You can instantiate the QuerySet
    as manager to your models to enable default filtering.

    Filter and sorting options passed through ``json_cfg`` and applied to ``filter_fields``:
        - ``sort_index`` List index of field to sort by.
        - ``sort_order`` Order fields by asc, desc or none.
        - ``filter_index`` List index of field to filter results. This displays all possible filter options.
        - ``selected_filter_index`` Field of filter to apply on queryset.
        - ``selected_filter_values`` Values to filter by on selected field.

    :var bool distinct_qs: Apply distinct filter option. Default is True.
    """
    distinct_qs = True

    def default_filter(self, opts, *args, **kwargs):
        """
        This is called by the view's ``get_queryset`` method.

        It calls the :func:`ajax_filter` first to apply the filter and then :func:`ajax_sort` to sort the filtered
        QuerySet. Each of these methods can be overridden to manipulate the QuerySet.

        :param opts: Filter options passed through request.
        :param args: Positional filter options in addition to opts.
        :param kwargs: Keword filter options in addition to opts.
        :return: Filtered QuerySet
        """
        return self.ajax_filter(opts, *args, **kwargs).ajax_sorter(opts)

    def ajax_filter(self, opts, *args, **kwargs):
        # args = set()
        # args.update((Q(field__isnull=True) | Q(field__name='none'),))
        filter_field = opts.get('filter_field', None)
        if isinstance(filter_field, tuple) and len(filter_field) == 2 and \
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
        """
        Used to get unique values of a given field.

        :param field: Name of the field
        :return: List of field values
        """
        return self.order_by(field).distinct(field).values_list(field, flat=True)
