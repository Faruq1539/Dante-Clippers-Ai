import React from 'react';
import { NavigationContainer, DarkTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import HomeScreen from '../screens/HomeScreen';
import UploadScreen from '../screens/UploadScreen';
import JobStatusScreen from '../screens/JobStatusScreen';
import ClipsScreen from '../screens/ClipsScreen';

export type RootStackParamList = {
  Home: undefined;
  Upload: undefined;
  JobStatus: { jobId: string };
  Clips: { jobId: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const theme = {
  ...DarkTheme,
  colors: { ...DarkTheme.colors, background: '#0B0B0F' },
};

export default function RootNavigator() {
  return (
    <NavigationContainer theme={theme}>
      <Stack.Navigator screenOptions={{ headerStyle: { backgroundColor: '#0B0B0F' }, headerTintColor: '#FFFFFF' }}>
        <Stack.Screen name="Home" component={HomeScreen} options={{ headerShown: false }} />
        <Stack.Screen name="Upload" component={UploadScreen} options={{ title: 'New Clip' }} />
        <Stack.Screen name="JobStatus" component={JobStatusScreen} options={{ title: 'Processing', headerBackVisible: false }} />
        <Stack.Screen name="Clips" component={ClipsScreen} options={{ title: 'Your Clips' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
