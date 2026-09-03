import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

import { creditsApi } from '../api';
import type { CreditBalance } from '../types';
import PrimaryButton from '../components/PrimaryButton';
import type { RootStackParamList } from '../navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'>;

/**
 * NOTE: this screen doesn't yet track a real job history locally -- the
 * backend doesn't have a "list my jobs" endpoint yet (only "list my
 * source videos" and "get one job by id"). For now this just shows the
 * credit balance and the upload entry point. Worth adding a
 * GET /jobs endpoint on the backend to populate a real history list here.
 */
export default function HomeScreen({ navigation }: Props) {
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBalance = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await creditsApi.balance();
      setBalance(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load balance');
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadBalance();
    }, [loadBalance])
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Dante Clippers AI</Text>

      <View style={styles.balanceCard}>
        <Text style={styles.balanceLabel}>Credits</Text>
        <Text style={styles.balanceValue}>{balance ? balance.credit_balance : '--'}</Text>
        {error && <Text style={styles.errorText}>{error}</Text>}
      </View>

      <PrimaryButton
        title="+ New Clip"
        onPress={() => navigation.navigate('Upload')}
        style={{ marginTop: 24 }}
      />

      <FlatList
        style={{ marginTop: 24 }}
        data={[]}
        keyExtractor={() => ''}
        renderItem={null}
        ListEmptyComponent={
          <Text style={styles.emptyText}>
            No clips yet. Tap "+ New Clip" to upload your first video.
          </Text>
        }
        refreshControl={<RefreshControl refreshing={loading} onRefresh={loadBalance} />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0B0B0F', padding: 20, paddingTop: 60 },
  title: { color: '#FFFFFF', fontSize: 28, fontWeight: '700', marginBottom: 24 },
  balanceCard: {
    backgroundColor: '#17171F',
    borderRadius: 16,
    padding: 20,
  },
  balanceLabel: { color: '#9A9AA5', fontSize: 14 },
  balanceValue: { color: '#FFFFFF', fontSize: 40, fontWeight: '700', marginTop: 4 },
  errorText: { color: '#FF6B6B', marginTop: 8, fontSize: 13 },
  emptyText: { color: '#6B6B76', textAlign: 'center', marginTop: 40, paddingHorizontal: 20 },
});
