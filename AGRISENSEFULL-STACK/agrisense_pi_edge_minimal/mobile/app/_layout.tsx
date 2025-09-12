import { Stack } from 'expo-router';
import { useEffect } from 'react';
import { Platform } from 'react-native';

export default function RootLayout() {
  useEffect(() => {
    if (Platform.OS === 'android') {
      // noop placeholder for any platform-specific init
    }
  }, []);

  return (
    <Stack>
      <Stack.Screen name="index" options={{ title: 'AgriSense' }} />
    </Stack>
  );
}
