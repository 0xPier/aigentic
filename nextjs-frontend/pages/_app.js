import * as React from 'react';
import PropTypes from 'prop-types';
import Head from 'next/head';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { CacheProvider } from '@emotion/react';
import theme from '../src/theme';
import createEmotionCache from '../src/createEmotionCache';
import Layout from '../components/Layout';
import { Alert, Box } from '@mui/material';

// Client-side cache, shared for the whole session of the user in the browser.
const clientSideEmotionCache = createEmotionCache();

export default function MyApp(props) {
  const { Component, emotionCache = clientSideEmotionCache, pageProps } = props;
  const [globalError, setGlobalError] = React.useState(null);

  // Function to set global error, can be called from any component
  const showGlobalError = (message) => {
    setGlobalError(message);
  };

  // Clear global error after some time
  React.useEffect(() => {
    if (globalError) {
      const timer = setTimeout(() => {
        setGlobalError(null);
      }, 5000); // Clear after 5 seconds
      return () => clearTimeout(timer);
    }
  }, [globalError]);

  return (
    <CacheProvider value={emotionCache}>
      <Head>
        <meta name="viewport" content="initial-scale=1, width=device-width" />
      </Head>
      <ThemeProvider theme={theme}>
        {/* CssBaseline kickstart an elegant, consistent, and simple baseline to build upon. */}
        <CssBaseline />
        <Layout>
          {globalError && (
            <Box sx={{ position: 'fixed', top: 70, left: '50%', transform: 'translateX(-50%)', zIndex: 9999 }}>
              <Alert severity="error">{globalError}</Alert>
            </Box>
          )}
          <Component {...pageProps} showGlobalError={showGlobalError} />
        </Layout>
      </ThemeProvider>
    </CacheProvider>
  );
}

MyApp.propTypes = {
  Component: PropTypes.elementType.isRequired,
  emotionCache: PropTypes.object,
  pageProps: PropTypes.object.isRequired,
};
