class Timekeeper(object):
    ''' Tracks the current time shared across Exchange classes.'''
    
    def __init__(self):
        self.timestamps = []
        self.current_timestamp = None
        self.still_add = True
        self.num_exchanges = 0
        self.current_ts_locations = []
        self.top_values = []
        self.initialized = False
    
    def initialize(self):
        if self.timestamps == []:
            raise Exception("No times contributed!")
        if not self.initialized:
            self.initialized = True
            self.increment_time()


    def get_time(self):
        ''' Get the current time as viewed by the timekeeper.'''
        if not self.initialized:
            raise Exception("Timekeeper.initialize must be called before get_time")
        return self.current_timestamp
    
    def increment_time(self):
        ''' Increment to the next time viewed by the timekeeper. '''
        if not self.initialized:
            raise Exception("Timekeeper.initialize must be called before get_time")
        if self.current_timestamp is None:
            #setup
            if self.timestamps == []:
                raise Exception("No times contributed!")
            self.still_add = False
            self.num_exchanges = len(self.timestamps)
            self.current_ts_locations = [0]*self.num_exchanges
            self.top_values = [0]*self.num_exchanges
            for x in range(0,self.num_exchanges):
                self.top_values[x] = self.timestamps[x][0]
            next_timestamp_index = self.top_values.index(min(self.top_values))
            self.current_timestamp = \
                self.timestamps[next_timestamp_index][self.current_ts_locations[next_timestamp_index]]
            self.current_ts_locations[next_timestamp_index] += 1
            self.top_values[next_timestamp_index] = \
                self.timestamps[next_timestamp_index][self.current_ts_locations[next_timestamp_index]]
            
        else:
            # first check that any times are remaining
            if self.timestamps == []:
                raise EOFError
            # go to next timestamp
            last_value = self.current_timestamp
            next_timestamp_index = self.top_values.index(min(self.top_values))
            self.current_timestamp = \
                self.timestamps[next_timestamp_index][self.current_ts_locations[next_timestamp_index]]
            if self.current_timestamp < last_value:
                print(self.current_timestamp)
                print(last_value)

            assert last_value <= self.current_timestamp
            if self.current_ts_locations[next_timestamp_index] + 1 == \
                len(self.timestamps[next_timestamp_index]):
                # when we run out of times, remove that index from arrays
                del self.timestamps[next_timestamp_index]
                del self.top_values[next_timestamp_index]

            else:
                self.current_ts_locations[next_timestamp_index] += 1
                self.top_values[next_timestamp_index] = \
                    self.timestamps[next_timestamp_index][self.current_ts_locations[next_timestamp_index]] 
                if self.current_timestamp == last_value:
                    self.increment_time()
        
    def contribute_times(self, timestamps):
        ''' Add a list of datetime objects to the timekeeper. The timekeeper steps 
        through all times provided via contribute_times.'''
        self.timestamps.append(timestamps)
