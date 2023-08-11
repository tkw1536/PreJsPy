module.exports = {
    overrides: [
        {
            files: ['*.ts'],
            extends: [
                'standard-with-typescript',
                'plugin:eslint-comments/recommended',
            ],
            rules: {
                "eslint-comments/no-unused-disable": "error",
            },
            parserOptions: {
                project: './tsconfig.json'
            }
        }
    ],
}