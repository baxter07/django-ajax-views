//noinspection BadExpressionStatementJS
({
    baseUrl: 'path/to/js/root/',
    name: 'almond',
    include: [
        'cs!middleware',
        'cs!mixins/view_name',
        'cs!views/view_name'
    ],
    exclude: ['coffee-script'],
    insertRequire: ['main'],
    stubModules: ['cs'],
    mainConfigFile: 'path/to/main.js',
    findNestedDependencies: true,
    // optimize: 'none',
    wrap: true
});