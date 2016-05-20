//noinspection BadExpressionStatementJS
({
    baseUrl: 'src',
    paths: {
        'coffee-script': '../../bower_components/coffeescript/extras/coffee-script',
        'cs': '../../bower_components/require-cs/cs'
    },
    include: [
        'cs!app',
        'cs!manager',
        'cs!middleware',
        'cs!view',
        'cs!plugins/filterview'
    ],
    exclude: ['coffee-script'],
    stubModules: ['cs'],
    transformAMDChecks: false,
    skipModuleInsertion: true,
    optimize: 'none',
    out: 'dist/ajaxviews.js',
    wrap: {
        startFile: 'wrap.start',
        endFile: 'wrap.end'
    },
    onModuleBundleComplete: function (data) {
        var fs = module.require('fs'),
            amdclean = module.require('amdclean');
        fs.writeFileSync(data.path, amdclean.clean({
            'filePath': data.path
        }));
    }
});