-- Flight Status Bot Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  language_code TEXT DEFAULT 'en',
  platform TEXT,
  version TEXT,
  first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Flights table
CREATE TABLE flights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flight_number TEXT NOT NULL,
  date DATE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(flight_number, date)
);

-- Flight details table
CREATE TABLE flight_details (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flight_id UUID REFERENCES flights(id) ON DELETE CASCADE,
  data_source TEXT,
  raw_data JSONB,
  normalized JSONB,
  last_checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Flight requests table
CREATE TABLE flight_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  flight_id UUID REFERENCES flights(id) ON DELETE CASCADE,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  flight_id UUID REFERENCES flights(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, flight_id)
);

-- Messages table
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id BIGINT,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  content TEXT,
  parsed_json JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature requests table
CREATE TABLE feature_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  feature_code TEXT NOT NULL,
  flight_id UUID REFERENCES flights(id) ON DELETE SET NULL,
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Flight logs table
CREATE TABLE flight_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flight_id UUID REFERENCES flights(id) ON DELETE CASCADE,
  status_before TEXT,
  status_after TEXT,
  event_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Translations table
CREATE TABLE translations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key TEXT NOT NULL,
  lang TEXT NOT NULL,
  value TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(key, lang)
);

-- Audit logs table
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  details JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_flights_number_date ON flights(flight_number, date);
CREATE INDEX idx_flight_details_flight_id ON flight_details(flight_id);
CREATE INDEX idx_flight_requests_user_id ON flight_requests(user_id);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_flight_id ON subscriptions(flight_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_feature_requests_user_id ON feature_requests(user_id);
CREATE INDEX idx_flight_logs_flight_id ON flight_logs(flight_id);
CREATE INDEX idx_translations_key_lang ON translations(key, lang);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Insert default translations
INSERT INTO translations (key, lang, value) VALUES
-- English translations
('label_status', 'en', 'Status'),
('label_codeshare', 'en', 'Also listed as'),
('label_terminal', 'en', 'Terminal'),
('label_checkin', 'en', 'Check-in'),
('label_gate', 'en', 'Gate'),
('label_boarding', 'en', 'Boarding'),
('label_departure', 'en', 'Departure'),
('label_arrival', 'en', 'Arrival'),
('label_landed', 'en', 'Landed'),
('label_belt', 'en', 'Belt'),
('label_aircraft', 'en', 'Aircraft'),
('label_was', 'en', 'was'),
('label_expected', 'en', 'expected'),
('welcome_message', 'en', '👋 Hello, {username}!\nI can help you track flight status.\nJust type flight number and date, for example:\n✈️ SU100 today\n📅 AFL123 05.07.2025'),
('parse_error', 'en', '⚠️ Sorry, I couldn''t recognize the flight number or date.\nPlease use the format like: SU100 today or SU100 05.07.2025'),
('no_date_request', 'en', 'I found flight number: {flight_number}.\nNow choose a date or type the date manually (DD.MM.YYYY):'),
('no_number_request', 'en', 'You entered a date: {date}\nPlease enter the flight number (e.g. QR123)'),
('future_flight', 'en', '📅 Flight {flight_number} on {date} is too far in the future.\nWe''ve saved your request and will notify you once data is available.'),
('past_flight', 'en', '❌ This flight is too far in the past.\nHistorical data is not yet supported.\n🚧 Feature under development.\n👇 Tap to request early access.'),
('new_search', 'en', 'Please enter flight number and date. For example: ''SU100 today'' or ''AFL123 05.07.2025'''),

-- Russian translations
('label_status', 'ru', 'Статус'),
('label_codeshare', 'ru', 'Также указан как'),
('label_terminal', 'ru', 'Терминал'),
('label_checkin', 'ru', 'Регистрация'),
('label_gate', 'ru', 'Выход'),
('label_boarding', 'ru', 'Посадка'),
('label_departure', 'ru', 'Вылет'),
('label_arrival', 'ru', 'Прилет'),
('label_landed', 'ru', 'Приземлился'),
('label_belt', 'ru', 'Лента'),
('label_aircraft', 'ru', 'Самолёт'),
('label_was', 'ru', 'было'),
('label_expected', 'ru', 'ожидалось'),
('welcome_message', 'ru', '👋 Привет, {username}!\nЯ помогу отследить статус рейса.\nПросто напиши номер рейса и дату, например:\n✈️ SU100 сегодня\n📅 AFL123 05.07.2025'),
('parse_error', 'ru', '⚠️ Извините, не удалось распознать номер рейса или дату.\nПожалуйста, используйте формат: SU100 сегодня или SU100 05.07.2025'),
('no_date_request', 'ru', 'Я нашел номер рейса: {flight_number}.\nТеперь выберите дату или введите дату вручную (ДД.ММ.ГГГГ):'),
('no_number_request', 'ru', 'Вы ввели дату: {date}\nПожалуйста, введите номер рейса (например QR123)'),
('future_flight', 'ru', '📅 Рейс {flight_number} на {date} слишком далеко в будущем.\nМы сохранили ваш запрос и уведомим, когда данные станут доступны.'),
('past_flight', 'ru', '❌ Этот рейс слишком далеко в прошлом.\nИсторические данные пока не поддерживаются.\n🚧 Функция в разработке.\n👇 Нажмите, чтобы запросить ранний доступ.'),
('new_search', 'ru', 'Пожалуйста, введите номер рейса и дату. Например: ''SU100 сегодня'' или ''AFL123 05.07.2025''');

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE flights ENABLE ROW LEVEL SECURITY;
ALTER TABLE flight_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE flight_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE flight_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE translations ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (we'll restrict later if needed)
CREATE POLICY "Allow all operations on users" ON users FOR ALL USING (true);
CREATE POLICY "Allow all operations on flights" ON flights FOR ALL USING (true);
CREATE POLICY "Allow all operations on flight_details" ON flight_details FOR ALL USING (true);
CREATE POLICY "Allow all operations on flight_requests" ON flight_requests FOR ALL USING (true);
CREATE POLICY "Allow all operations on subscriptions" ON subscriptions FOR ALL USING (true);
CREATE POLICY "Allow all operations on messages" ON messages FOR ALL USING (true);
CREATE POLICY "Allow all operations on feature_requests" ON feature_requests FOR ALL USING (true);
CREATE POLICY "Allow all operations on flight_logs" ON flight_logs FOR ALL USING (true);
CREATE POLICY "Allow all operations on translations" ON translations FOR ALL USING (true);
CREATE POLICY "Allow all operations on audit_logs" ON audit_logs FOR ALL USING (true); 