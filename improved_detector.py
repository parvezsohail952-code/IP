"""
IMPROVED Behavior-Based Insider Threat Detection System
========================================================

Enhancements:
- More realistic behavioral patterns
- Better feature engineering
- Improved anomaly detection with ensemble methods
- Lower false positive rate through better tuning
- Additional attack scenarios
- Time-series analysis
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from scipy import stats
import json
import warnings
warnings.filterwarnings('ignore')


class ImprovedFlowGenerator:
    """Enhanced traffic generator with more realistic patterns"""
    
    def __init__(self, seed=42):
        np.random.seed(seed)
        
    def generate_normal_traffic(self, user, department='engineering', n_flows=1000, days=30):
        """
        Generate realistic normal behavior based on department and role.
        Longer baseline period (30 days) for better profiling.
        """
        flows = []
        start_date = datetime.now() - timedelta(days=days)
        
        # Department-specific patterns
        dept_patterns = {
            'engineering': {
                'work_start': 9, 'work_end': 18,
                'avg_bytes': 800000, 'std_bytes': 200000,
                'avg_duration': 600, 'destinations_per_day': 25,
                'external_ratio': 0.6  # Engineers access external resources often
            },
            'hr': {
                'work_start': 8, 'work_end': 17,
                'avg_bytes': 200000, 'std_bytes': 50000,
                'avg_duration': 180, 'destinations_per_day': 10,
                'external_ratio': 0.3
            },
            'finance': {
                'work_start': 8, 'work_end': 19,  # Longer hours
                'avg_bytes': 500000, 'std_bytes': 100000,
                'avg_duration': 400, 'destinations_per_day': 15,
                'external_ratio': 0.4
            },
            'sales': {
                'work_start': 9, 'work_end': 18,
                'avg_bytes': 300000, 'std_bytes': 80000,
                'avg_duration': 300, 'destinations_per_day': 30,
                'external_ratio': 0.7  # Sales contacts many external clients
            }
        }
        
        pattern = dept_patterns.get(department, dept_patterns['engineering'])
        
        for i in range(n_flows):
            # Realistic daily patterns
            day_offset = np.random.randint(0, days)
            weekday = (start_date + timedelta(days=day_offset)).weekday()
            
            # Skip most weekend traffic
            if weekday >= 5 and np.random.random() > 0.1:
                continue
            
            # Working hours with natural variation
            hour = np.random.normal(
                (pattern['work_start'] + pattern['work_end']) / 2,
                2.5
            )
            hour = np.clip(hour, pattern['work_start'], pattern['work_end'])
            
            # Small chance of legitimate off-hours work
            if np.random.random() < 0.05:  # 5% off-hours
                hour = np.random.choice([7, 8, 19, 20, 21])
            
            timestamp = start_date + timedelta(
                days=day_offset,
                hours=int(hour),
                minutes=np.random.randint(0, 60),
                seconds=np.random.randint(0, 60)
            )
            
            # Determine if external or internal destination
            is_external = np.random.random() < pattern['external_ratio']
            
            if is_external:
                dst_ip = self._generate_external_ip()
                dst_port = np.random.choice([443, 80], p=[0.8, 0.2])  # Mostly HTTPS
            else:
                dst_ip = f"10.0.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
                dst_port = np.random.choice([443, 80, 445, 3389, 22], p=[0.4, 0.2, 0.2, 0.1, 0.1])
            
            # Realistic flow characteristics
            packet_count = int(np.random.lognormal(4, 1))  # Log-normal distribution
            byte_count = int(np.random.normal(pattern['avg_bytes'], pattern['std_bytes']))
            byte_count = max(byte_count, 100)  # Minimum packet size
            
            duration = np.random.exponential(pattern['avg_duration'])
            flow_rate = packet_count / max(duration, 1)
            
            flow = {
                'user': user,
                'timestamp': timestamp,
                'src_ip': f'10.0.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}',
                'dst_ip': dst_ip,
                'dst_port': int(dst_port),
                'protocol': 'TCP',
                'packet_count': packet_count,
                'byte_count': byte_count,
                'duration': duration,
                'flow_rate': flow_rate,
                'is_external': is_external,
                'department': department,
                'is_malicious': False
            }
            
            flows.append(flow)
        
        return flows
    
    def generate_data_exfiltration(self, user, n_flows=150):
        """
        Data exfiltration: Large uploads to cloud storage / external sites
        Key indicators: off-hours, large volumes, sustained transfers
        """
        flows = []
        current_time = datetime.now()
        
        # Cloud storage destinations (common exfiltration targets)
        cloud_ips = [
            '52.216.', '52.92.',   # AWS S3
            '172.253.', '142.250.', # Google Drive
            '13.107.', '40.126.',   # OneDrive
        ]
        
        for i in range(n_flows):
            # Spread over multiple nights (stealthy exfiltration)
            night_offset = np.random.randint(0, 5)  # 5 nights
            hour = int(np.random.choice([22, 23, 0, 1, 2, 3, 4, 5]))
            
            timestamp = current_time + timedelta(
                days=night_offset,
                hours=hour - current_time.hour,
                minutes=int(np.random.randint(0, 60))
            )
            
            # Large sustained uploads
            packet_count = int(np.random.normal(800, 150))
            byte_count = int(np.random.normal(8000000, 2000000))  # 8MB avg
            duration = np.random.normal(2400, 600)  # 40 min avg
            
            flow = {
                'user': user,
                'timestamp': timestamp,
                'src_ip': f'10.0.{int(np.random.randint(1, 255))}.{int(np.random.randint(1, 255))}',
                'dst_ip': f"{np.random.choice(cloud_ips)}{np.random.randint(0, 255)}.{np.random.randint(1, 255)}",
                'dst_port': 443,
                'protocol': 'TCP',
                'packet_count': packet_count,
                'byte_count': byte_count,
                'duration': duration,
                'flow_rate': packet_count / duration,
                'is_external': True,
                'is_malicious': True,
                'attack_type': 'data_exfiltration'
            }
            flows.append(flow)
        
        return flows
    
    def generate_lateral_movement(self, user, n_flows=200):
        """
        Lateral movement: Network reconnaissance and unauthorized access attempts
        """
        flows = []
        current_time = datetime.now()
        
        # Admin ports commonly targeted
        admin_ports = [22, 23, 135, 139, 445, 3389, 5900, 5985, 5986]
        
        for i in range(n_flows):
            timestamp = current_time + timedelta(seconds=i*3)  # Rapid succession
            
            # Scan different internal hosts
            target_ip = f"10.0.{int(np.random.randint(1, 255))}.{int(np.random.randint(1, 255))}"
            target_port = int(np.random.choice(admin_ports))
            
            # Small probe packets
            packet_count = int(np.random.normal(5, 2))
            byte_count = int(np.random.normal(300, 100))
            duration = np.random.uniform(0.1, 3)  # Very short connections
            
            flow = {
                'user': user,
                'timestamp': timestamp,
                'src_ip': f'10.0.{int(np.random.randint(1, 255))}.{int(np.random.randint(1, 255))}',
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'packet_count': packet_count,
                'byte_count': byte_count,
                'duration': duration,
                'flow_rate': packet_count / duration,
                'is_external': False,
                'is_malicious': True,
                'attack_type': 'lateral_movement'
            }
            flows.append(flow)
        
        return flows
    
    def generate_credential_theft(self, user, n_flows=80):
        """
        Credential theft: Accessing authentication servers, dumping credentials
        """
        flows = []
        current_time = datetime.now()
        
        # Domain controllers and auth servers
        dc_ips = [f"10.0.1.{i}" for i in [10, 11, 12, 20]]
        auth_ports = [88, 389, 636, 3268, 3269]  # Kerberos, LDAP
        
        for i in range(n_flows):
            hour = int(np.random.choice([2, 3, 4, 22, 23]))  # Late night
            timestamp = current_time + timedelta(
                hours=hour - current_time.hour,
                minutes=int(np.random.randint(0, 60))
            )
            
            flow = {
                'user': user,
                'timestamp': timestamp,
                'src_ip': f'10.0.{int(np.random.randint(1, 255))}.{int(np.random.randint(1, 255))}',
                'dst_ip': np.random.choice(dc_ips),
                'dst_port': int(np.random.choice(auth_ports)),
                'protocol': 'TCP',
                'packet_count': int(np.random.normal(150, 30)),
                'byte_count': int(np.random.normal(100000, 20000)),
                'duration': np.random.normal(180, 40),
                'flow_rate': 0.8,
                'is_external': False,
                'is_malicious': True,
                'attack_type': 'credential_theft'
            }
            flows.append(flow)
        
        return flows
    
    def _generate_external_ip(self):
        """Generate realistic external IPs"""
        external_ranges = [
            '52.', '54.',      # AWS
            '172.217.', '172.253.',  # Google
            '13.', '40.',      # Azure
            '151.101.',        # Fastly CDN
            '104.16.',         # Cloudflare
        ]
        prefix = np.random.choice(external_ranges)
        return f"{prefix}{np.random.randint(0, 255)}.{np.random.randint(1, 255)}"


class AdvancedBehavioralProfiler:
    """Enhanced profiling with more sophisticated features"""
    
    def __init__(self):
        self.user_profiles = {}
        self.scaler = RobustScaler()  # More robust to outliers
        
    def extract_features(self, flows_df):
        """
        Extract 20+ behavioral features with better discriminative power
        """
        features_list = []
        
        for user in flows_df['user'].unique():
            user_flows = flows_df[flows_df['user'] == user]
            
            # === TEMPORAL FEATURES ===
            user_flows['hour'] = pd.to_datetime(user_flows['timestamp']).dt.hour
            user_flows['weekday'] = pd.to_datetime(user_flows['timestamp']).dt.weekday
            
            # Work hours (9-17) ratio
            work_hours_ratio = len(user_flows[(user_flows['hour'] >= 9) & 
                                               (user_flows['hour'] <= 17)]) / len(user_flows)
            
            # Off-hours (22-06) ratio - KEY INDICATOR
            off_hours_ratio = len(user_flows[(user_flows['hour'] >= 22) | 
                                              (user_flows['hour'] <= 6)]) / len(user_flows)
            
            # Weekend activity ratio
            weekend_ratio = len(user_flows[user_flows['weekday'] >= 5]) / len(user_flows)
            
            # Hour entropy
            hour_entropy = self._calculate_entropy(user_flows['hour'].value_counts(normalize=True))
            
            # === VOLUME FEATURES ===
            avg_bytes = user_flows['byte_count'].mean()
            std_bytes = user_flows['byte_count'].std()
            max_bytes = user_flows['byte_count'].max()
            p95_bytes = user_flows['byte_count'].quantile(0.95)
            
            avg_packets = user_flows['packet_count'].mean()
            std_packets = user_flows['packet_count'].std()
            
            # Total data transfer
            total_bytes = user_flows['byte_count'].sum()
            
            # === DIVERSITY FEATURES ===
            unique_dsts = user_flows['dst_ip'].nunique()
            unique_ports = user_flows['dst_port'].nunique()
            
            dst_entropy = self._calculate_entropy(user_flows['dst_ip'].value_counts(normalize=True))
            port_entropy = self._calculate_entropy(user_flows['dst_port'].value_counts(normalize=True))
            
            # === SESSION FEATURES ===
            avg_duration = user_flows['duration'].mean()
            std_duration = user_flows['duration'].std()
            max_duration = user_flows['duration'].max()
            
            avg_flow_rate = user_flows['flow_rate'].mean()
            
            # === EXTERNAL COMMUNICATION ===
            if 'is_external' in user_flows.columns:
                external_ratio = user_flows['is_external'].mean()
                external_bytes = user_flows[user_flows['is_external']]['byte_count'].sum()
            else:
                external_ratio = 0
                external_bytes = 0
            
            # === ADVANCED FEATURES ===
            # Burst detection: sessions per hour
            flows_per_hour = len(user_flows) / (
                (user_flows['timestamp'].max() - user_flows['timestamp'].min()).total_seconds() / 3600 + 1
            )
            
            # Connection diversity score
            connection_diversity = unique_dsts / len(user_flows) if len(user_flows) > 0 else 0
            
            features = {
                'user': user,
                # Temporal
                'work_hours_ratio': work_hours_ratio,
                'off_hours_ratio': off_hours_ratio,
                'weekend_ratio': weekend_ratio,
                'hour_entropy': hour_entropy,
                # Volume
                'avg_bytes': avg_bytes,
                'std_bytes': std_bytes,
                'max_bytes': max_bytes,
                'p95_bytes': p95_bytes,
                'avg_packets': avg_packets,
                'total_bytes': total_bytes,
                # Diversity
                'unique_destinations': unique_dsts,
                'unique_ports': unique_ports,
                'dst_entropy': dst_entropy,
                'port_entropy': port_entropy,
                # Session
                'avg_duration': avg_duration,
                'std_duration': std_duration,
                'max_duration': max_duration,
                'avg_flow_rate': avg_flow_rate,
                # External
                'external_ratio': external_ratio,
                'external_bytes': external_bytes,
                # Advanced
                'flows_per_hour': flows_per_hour,
                'connection_diversity': connection_diversity,
                'total_flows': len(user_flows)
            }
            
            features_list.append(features)
        
        return pd.DataFrame(features_list)
    
    def build_profiles(self, baseline_flows_df):
        """Build behavioral profiles"""
        features_df = self.extract_features(baseline_flows_df)
        
        for _, row in features_df.iterrows():
            user = row['user']
            self.user_profiles[user] = {
                'baseline_features': row.drop('user').to_dict(),
                'profile_created': datetime.now()
            }
        
        return features_df
    
    def _calculate_entropy(self, probabilities):
        """Shannon entropy"""
        probabilities = probabilities[probabilities > 0]
        if len(probabilities) == 0:
            return 0
        return -np.sum(probabilities * np.log2(probabilities))


class EnsembleAnomalyDetector:
    """
    Ensemble detector combining multiple methods for better accuracy
    """
    
    def __init__(self, contamination=0.08):  # Reduced from 0.15
        self.contamination = contamination
        
        # Multiple detectors
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=150,  # More trees
            max_samples=256
        )
        
        self.scaler = RobustScaler()
        self.baseline_stats = {}
        self.fitted = False
        
    def fit(self, baseline_features_df):
        """Train ensemble"""
        feature_cols = [col for col in baseline_features_df.columns if col != 'user']
        X = baseline_features_df[feature_cols].fillna(0)
        
        # Store statistics
        self.baseline_stats = {
            'mean': X.mean().to_dict(),
            'std': X.std().to_dict(),
            'median': X.median().to_dict(),
            'mad': (X - X.median()).abs().median().to_dict()
        }
        
        # Fit scaler and model
        X_scaled = self.scaler.fit_transform(X)
        self.isolation_forest.fit(X_scaled)
        
        self.feature_cols = feature_cols
        self.fitted = True
        
        return self
    
    def detect(self, current_features_df):
        """Detect anomalies using ensemble voting"""
        if not self.fitted:
            raise ValueError("Must fit first!")
        
        X = current_features_df[self.feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # Method 1: Isolation Forest
        if_predictions = self.isolation_forest.predict(X_scaled)
        if_scores = -self.isolation_forest.score_samples(X_scaled)
        
        # Method 2: Statistical deviation (MAD-based)
        mad_scores = self._calculate_mad_scores(X)
        
        # Method 3: Feature-specific thresholds
        threshold_violations = self._check_thresholds(X)
        
        # Ensemble: Combine scores
        combined_scores = (if_scores * 0.5 + mad_scores * 0.3 + threshold_violations * 0.2)
        
        # More conservative threshold
        anomaly_threshold = np.percentile(combined_scores, 85)  # Top 15%
        is_anomaly = combined_scores > anomaly_threshold
        
        results = current_features_df.copy()
        results['anomaly_score'] = combined_scores
        results['is_anomaly'] = is_anomaly
        results['if_score'] = if_scores
        results['mad_score'] = mad_scores
        results['threshold_violations'] = threshold_violations
        results['risk_level'] = results['anomaly_score'].apply(self._classify_risk)
        
        return results
    
    def _calculate_mad_scores(self, X):
        """Median Absolute Deviation scores (robust to outliers)"""
        mad_scores = []
        
        for _, row in X.iterrows():
            total_deviation = 0
            for col in self.feature_cols:
                median = self.baseline_stats['median'][col]
                mad = self.baseline_stats['mad'][col]
                
                if mad > 0:
                    deviation = abs(row[col] - median) / mad
                    total_deviation += deviation
            
            mad_scores.append(total_deviation / len(self.feature_cols))
        
        # Normalize to [0, 1]
        mad_scores = np.array(mad_scores)
        if mad_scores.max() > 0:
            mad_scores = mad_scores / mad_scores.max()
        
        return mad_scores
    
    def _check_thresholds(self, X):
        """Check critical feature thresholds"""
        violations = []
        
        for _, row in X.iterrows():
            score = 0
            
            # Critical indicators
            if row.get('off_hours_ratio', 0) > 0.3:  # >30% off-hours
                score += 0.3
            if row.get('max_bytes', 0) > 5000000:  # >5MB transfers
                score += 0.2
            if row.get('external_ratio', 0) > 0.9:  # >90% external
                score += 0.2
            if row.get('flows_per_hour', 0) > 200:  # High burst
                score += 0.2
            if row.get('unique_destinations', 0) > 150:  # Too many destinations
                score += 0.1
            
            violations.append(score)
        
        return np.array(violations)
    
    def _classify_risk(self, anomaly_score):
        """Conservative risk classification"""
        if anomaly_score > 0.8:
            return 'CRITICAL'
        elif anomaly_score > 0.6:
            return 'HIGH'
        elif anomaly_score > 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'


def run_improved_detection():
    """Main improved detection pipeline"""
    print("\n" + "="*80)
    print("IMPROVED INSIDER THREAT DETECTION SYSTEM v2.0")
    print("="*80 + "\n")
    
    generator = ImprovedFlowGenerator()
    profiler = AdvancedBehavioralProfiler()
    detector = EnsembleAnomalyDetector(contamination=0.08)
    
    # Phase 1: Generate larger baseline (30 days, 10 users)
    print("Phase 1: Generating baseline traffic (30 days, 10 users)...")
    
    normal_users = [
        ('alice', 'engineering'),
        ('bob', 'engineering'),
        ('charlie', 'hr'),
        ('david', 'finance'),
        ('frank', 'sales'),
        ('grace', 'engineering'),
        ('ivan', 'hr'),
        ('julia', 'finance')
    ]
    
    baseline_flows = []
    for user, dept in normal_users:
        flows = generator.generate_normal_traffic(user, dept, n_flows=1200, days=30)
        baseline_flows.extend(flows)
        print(f"  ✓ {user} ({dept}): {len(flows)} flows")
    
    baseline_df = pd.DataFrame(baseline_flows)
    print(f"\n  Total baseline flows: {len(baseline_df)}")
    
    # Phase 2: Build profiles
    print("\nPhase 2: Building behavioral profiles...")
    baseline_features = profiler.build_profiles(baseline_df)
    print(f"  ✓ Created profiles for {len(baseline_features)} users")
    print(f"  ✓ Features extracted: {len(baseline_features.columns) - 1}")
    
    # Phase 3: Train detector
    print("\nPhase 3: Training ensemble detector...")
    detector.fit(baseline_features)
    print("  ✓ Isolation Forest trained")
    print("  ✓ Statistical baselines established")
    print("  ✓ Threshold rules configured")
    
    # Phase 4: Generate test traffic with attacks
    print("\nPhase 4: Generating test traffic...")
    
    test_flows = []
    
    # Normal users continue
    for user, dept in normal_users[:6]:
        flows = generator.generate_normal_traffic(user, dept, n_flows=200, days=1)
        test_flows.extend(flows)
        print(f"  ✓ {user}: Normal activity")
    
    # Insider threats
    eve_flows = generator.generate_data_exfiltration('eve', n_flows=150)
    test_flows.extend(eve_flows)
    print(f"  🚨 eve: Data exfiltration attack (150 flows)")
    
    helen_flows = generator.generate_lateral_movement('helen', n_flows=120)
    test_flows.extend(helen_flows)
    print(f"  🚨 helen: Lateral movement attack (120 flows)")
    
    mallory_flows = generator.generate_credential_theft('mallory', n_flows=80)
    test_flows.extend(mallory_flows)
    print(f"  🚨 mallory: Credential theft attack (80 flows)")
    
    test_df = pd.DataFrame(test_flows)
    
    # Phase 5: Detect
    print("\nPhase 5: Running detection...")
    test_features = profiler.extract_features(test_df)
    results = detector.detect(test_features)
    
    # Phase 6: Evaluate
    print("\n" + "="*80)
    print("DETECTION RESULTS")
    print("="*80 + "\n")
    
    # Merge with ground truth
    test_labels = test_df.groupby('user').agg({'is_malicious': 'max'}).reset_index()
    evaluation = results.merge(test_labels, on='user', how='left')
    evaluation['is_malicious'] = evaluation['is_malicious'].fillna(False)
    
    # Calculate metrics
    tp = len(evaluation[(evaluation['is_anomaly']) & (evaluation['is_malicious'])])
    fp = len(evaluation[(evaluation['is_anomaly']) & (~evaluation['is_malicious'])])
    tn = len(evaluation[(~evaluation['is_anomaly']) & (~evaluation['is_malicious'])])
    fn = len(evaluation[(~evaluation['is_anomaly']) & (evaluation['is_malicious'])])
    
    accuracy = (tp + tn) / (tp + tn + fp + fn) * 100 if (tp + tn + fp + fn) > 0 else 0
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0
    
    # Display results
    print(f"{'User':<12} {'Anomaly Score':<15} {'Risk':<12} {'Detected':<12} {'Actual Threat':<15}")
    print("-"*80)
    
    for _, row in evaluation.iterrows():
        detected = "🚨 YES" if row['is_anomaly'] else "   NO"
        actual = "✓ YES" if row['is_malicious'] else "  NO"
        print(f"{row['user']:<12} {row['anomaly_score']:.4f}          {row['risk_level']:<12} {detected:<12} {actual:<15}")
    
    print("\n" + "="*80)
    print("PERFORMANCE METRICS")
    print("="*80)
    print(f"\nAccuracy:              {accuracy:.2f}%")
    print(f"Precision:             {precision:.2f}%")
    print(f"Recall (TPR):          {recall:.2f}%")
    print(f"F1-Score:              {f1:.2f}%")
    print(f"False Positive Rate:   {fpr:.2f}%")
    
    print(f"\n{'Metric':<20} {'Count':<10}")
    print("-"*30)
    print(f"{'True Positives':<20} {tp:<10}")
    print(f"{'False Positives':<20} {fp:<10}")
    print(f"{'True Negatives':<20} {tn:<10}")
    print(f"{'False Negatives':<20} {fn:<10}")
    
    # Save detailed report
    report = {
        'metrics': {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'false_positive_rate': fpr,
            'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn
        },
        'detections': evaluation.to_dict('records')
    }
    
    with open('/home/claude/improved_detection_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n✓ Detailed report saved to: improved_detection_report.json")
    print("="*80 + "\n")
    
    return evaluation, report


if __name__ == "__main__":
    evaluation, report = run_improved_detection()
