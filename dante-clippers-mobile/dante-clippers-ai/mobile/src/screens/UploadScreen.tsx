import React, { useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { videosApi, jobsApi } from '../api';
import { ApiError } from '../api/client';
import PrimaryButton from '../components/PrimaryButton';
import type { RootStackParamList } from '../navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'Upload'>;

type Stage = 'idle' | 'uploading' | 'starting_job';

export default function UploadScreen({ navigation }: Props) {
  const [stage, setStage] = useState<Stage>('idle');

  async function pickAndUpload() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission needed', 'Allow access to your videos to continue.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      quality: 1,
    });

    if (result.canceled || !result.assets?.length) {
      return;
    }

    const asset = result.assets[0];
    const fileName = asset.fileName || `video-${Date.now()}.mp4`;

    try {
      setStage('uploading');
      const video = await videosApi.upload(asset.uri, fileName, 'video/mp4');

      setStage('starting_job');
      const job = await jobsApi.create(video.id);

      navigation.replace('JobStatus', { jobId: job.id });
    } catch (e) {
      const message =
        e instanceof ApiError && e.status === 402
          ? "You don't have enough credits for a video this long. Check your balance on the home screen."
          : e instanceof Error
            ? e.message
            : 'Something went wrong.';
      Alert.alert('Upload failed', message);
    } finally {
      setStage('idle');
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Create a Clip</Text>
      <Text style={styles.subtitle}>
        Pick a video from your camera roll. We'll find the best moments and turn them into
        share-ready shorts.
      </Text>

      {stage === 'idle' ? (
        <PrimaryButton title="Choose Video" onPress={pickAndUpload} style={{ marginTop: 32 }} />
      ) : (
        <View style={styles.loadingBox}>
          <ActivityIndicator color="#FFFFFF" size="large" />
          <Text style={styles.loadingText}>
            {stage === 'uploading' ? 'Uploading video…' : 'Starting processing…'}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0B0B0F', padding: 20, paddingTop: 60 },
  title: { color: '#FFFFFF', fontSize: 24, fontWeight: '700' },
  subtitle: { color: '#9A9AA5', fontSize: 15, marginTop: 8, lineHeight: 21 },
  loadingBox: { marginTop: 48, alignItems: 'center' },
  loadingText: { color: '#9A9AA5', marginTop: 16, fontSize: 15 },
});
