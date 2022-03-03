const path = require('path');
const { ESBuildMinifyPlugin } = require('esbuild-loader')

const dev = {
    entry: './src/index.ts',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'build.js'
    },
    resolve: {
        extensions: ['.ts', '.js'],
        fallback: {
            crypto: require.resolve("crypto-browserify"),
            buffer: require.resolve("buffer"),
            stream: require.resolve("stream-browserify")
        }
    },
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                loader: 'esbuild-loader',
                options: {
                    loader: 'ts',
                    target: 'ESNext'
                },
                exclude: /node_modules/
            }
        ]
    },
    optimization: {
        minimizer: [
            new ESBuildMinifyPlugin({
                target: 'ESNext'
            })
        ]
    },
    devServer: {
        static: path.join(__dirname, 'dist'),
        compress: true,
        port: 9000,
        allowedHosts: "localhost",
        hot: false,
        liveReload: false
    }
};

const prod = {
    entry: './src/index.ts',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'prod.build.js'
    },
    resolve: {
        extensions: ['.ts', '.js'],
        fallback: {
            crypto: require.resolve("crypto-browserify"),
            buffer: require.resolve("buffer"),
            stream: require.resolve("stream-browserify")
        }
    },
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                loader: 'esbuild-loader',
                options: {
                    loader: 'ts',
                    target: 'ESNext'
                },
                exclude: /node_modules/
            }
        ]
    },
    optimization: {
        minimize: true
    }
};

module.exports = (_, argv) => {
    return argv.mode === 'production'
        ? prod
        : dev;
}