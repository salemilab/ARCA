import sys
import arcadb
from datetime import datetime
import xlsxwriter

def cleanCountryName(name):
    return name.replace(" ", "_").replace("(", "_").replace(")", "")

def timestamp():
    return int(datetime.utcnow().timestamp())

class Results(object):
    countryid = 0
    country = ""
    virus_ids = []
    viruses = []
    rawdata = []
    data = {}
    keys = None
    headers = []
    colnames = []
    rowformat = None
    csvfile = ""
    tsvfile = ""
    xlsfile = ""
    viruscolors = ["",          # Virus IDs start at 1
                   "rgb(255, 140, 0)",
                   "rgb(0,   128, 0)",
                   "rgb(148, 0,   211)"]
    
    def __init__(self, countryid):
        self.countryid = countryid
        self.virus_ids = []
        self.viruses = []
        self.rawdata = []
        self.data = {}
        self.keys = set()
        self.headers = []

    def clone(self):
        new = Results(self.countryid)
        new.country = "Total"
        new.virus_ids = self.virus_ids
        new.viruses = self.viruses
        new.headers = self.headers
        new.colnames = self.colnames
        new.rowformat = self.rowformat
        ts = timestamp()
        new.csvfile = "Total_{}.csv".format(ts)
        new.tsvfile = "Total_{}.tsv".format(ts)
        new.xlsfile = "Total_{}.xlsx".format(ts)
        return new
    
    def query(self, db, virus_ids, start_year, start_week, end_year, end_week):
        self.country = arcadb.getCountryName(db, self.countryid)
        clean = cleanCountryName(self.country)
        ts = timestamp()
        self.csvfile = "{}_{}.csv".format(clean, ts)
        self.tsvfile = "{}_{}.tsv".format(clean, ts)
        self.xlsfile = "{}_{}.xlsx".format(clean, ts)

        self.virus_ids = virus_ids
        self.viruses = arcadb.getVirusNames(db, virus_ids)
        self.rawdata = arcadb.getCases(db, self.countryid, virus_ids, start_year, start_week, end_year, end_week)

        self.headers = "<TR class='w3-green'><TH>Year</TH><TH class='w3-right-align'>Week</TH>"
        self.colnames = ["Country", "Year", "Week"]
        self.rowformat = "<TR><TD>{}</TD><TD class='w3-right-align'>{}</TD>"
        for v in self.viruses:
            self.headers += "<TH class='w3-right-align'>" + v + "</TH>"
            self.colnames.append(v)
            self.rowformat += "<TD class='w3-right-align'>{}</TD>"
        self.headers += "</TR>\n"
        self.rowformat += "</TR>\n"

        ncolumns = len(self.viruses)
        #row = ["", ""] + ["NR"]*ncolumns
        vp = {}
        pos = 2
        for v in self.virus_ids:
            vp[int(v)] = pos
            pos += 1

        for rd in self.rawdata:
            #sys.stdout.write("{}<BR>".format(rd))
            if rd[0] == start_year and rd[1] < start_week:
                continue
            if rd[0] == end_year and rd[1] > end_week:
                continue

            key = "{}_{:02}".format(rd[0], rd[1])
            if key in self.data:
                row = self.data[key]
            else:
                row = [rd[0], rd[1]] + ["NR"]*ncolumns
                self.data[key] = row
                self.keys.add(key)
            virus = rd[2]
            field = vp[virus]
            #sys.stdout.write("{}\n".format(field))
            row[field] = "{:,}".format(rd[3])
        #self.data.append(row)

    def add(self, other):
        ncolumns = len(self.viruses)
        newdata = {}
        keyset = self.keys.union(other.keys)
        keys = list(keyset)
        keys.sort()
        for k in keys:
            d1 = self.data[k] if k in self.data else None
            d2 = other.data[k] if k in other.data else None
            if d1 and d2:
                for i in range(ncolumns):
                    v1 = d1[i+2]
                    v2 = d2[i+2]
                    if v1 == "NR" and v2 == "NR":
                        nv = "NR"
                    elif v1 == "NR":
                        nv = v2
                    elif v2 == "NR":
                        nv = v1
                    else:
                        nv = "{:,}".format(int(v1.replace(",", "")) + int(v2.replace(",", "")))
                    d1[i+2] = nv
                newdata[k] = d1
            elif d1:
                newdata[k] = d1
            else:
                newdata[k] = d2
        self.data = newdata
        self.keys = keyset
                
    def generate_plot(self, divname, uselog=False, smooth=True):
        line = "spline" if smooth else "linear"
        nviruses = len(self.virus_ids)
        ntrace = 1
        traces = []
        sys.stdout.write("""function draw_{}() {{""".format(divname))
        for i in range(nviruses):
            j = i + 2
            virus_name = self.viruses[i]
            tracename = "trace" + str(ntrace)
            traces.append(tracename)

            xs = []
            ys = []
            for k in sorted(self.data.keys()):
                row = self.data[k]
                xs.append("{:.2f}".format(row[0] + row[1] / 52))
                y = row[j]
                if y == "NR":
                    ys.append("0")
                else:
                    ys.append(y.replace(",", ""))
                          
            sys.stdout.write("""
 var {} = {{
  x: [{}],
  y: [{}],
  type: 'scatter',
  line: {{
    color: '{}',            
    shape: '{}'
  }},
  name: '{}',
}};

""".format(tracename, ",".join(xs), ",".join(ys), self.viruscolors[int(self.virus_ids[i])], line, virus_name))
            ntrace += 1
        logaxis = """  yaxis: {
    type: 'log',
    autorange: true
  },
"""

        sys.stdout.write("""
var data = [{}];

var layout = {{
  title: '{}',
  xaxis: {{
    tickangle: -90
  }},
  {}
  barmode: 'group',
}};

Plotly.newPlot('{}', data, layout);
}}
""".format(", ".join(traces), self.country, logaxis if uselog else "", divname))


    def write_to_file(self, filename, delimiter=',', countries=None):
        with open(filename, "w") as out:
            if countries:
                out.write("# The following sheet contains total cases for the following countries:\n")
                for c in countries:
                    out.write("# " + c + "\n")
            out.write(delimiter.join(self.colnames) + "\n")
            for k in sorted(self.data.keys()):
                row = self.data[k]
                out.write(self.country + delimiter + delimiter.join([str(x) for x in row]) + "\n")
                
    def write_to_excel(self, filename, countries=None):
        wb = xlsxwriter.Workbook(filename, {'strings_to_numbers': True})
        ### workbook.set_properties({'author': 'A. Riva, ariva@ufl.edu', 'company': 'DiBiG - ICBR Bioinformatics'}) # these should be read from conf or command-line
        bold = wb.add_format({'bold': 1})

        if countries:
            ws = wb.add_worksheet("Countries")
            ws.write(0, 0, "The following sheet contains total cases for the following countries:")
            row = 2
            for c in countries:
                ws.write(row, 0, c)
                row += 1
        
        ws = wb.add_worksheet("Cases")
        row = 0
        col = 0
        for cn in self.colnames:
            ws.write(row, col, self.colnames[col], bold)
            col += 1

        r = 1
        for k in sorted(self.data.keys()):
            row = self.data[k]
            ws.write(r, 0, self.country)
            col = 1
            for x in row:
                ws.write(r, col, x)
                col += 1
            r += 1
        wb.close()
        
def multi_country_plot(divname, countrydata, uselog, smooth):
    C1 = countrydata[0]
    virus_name = C1.viruses[0]
    line = "spline" if smooth else "linear"
    
    traces = []
    idx = 1
    
    sys.stdout.write("""function draw_{}() {{""".format(divname))
    for C in countrydata:
        xs = []
        ys = []
        tracename = "ttrace_" + str(idx)
        traces.append(tracename)
        
        for k in sorted(C.data.keys()):
            row = C.data[k]
            xs.append("{:.2f}".format(row[0] + row[1] / 52))
            y = row[2]
            if y == "NR":
                ys.append("0")
            else:
                ys.append(y.replace(",", ""))

        sys.stdout.write("""
 var {} = {{
  x: [{}],
  y: [{}],
  type: 'scatter',
  line: {{
    shape: '{}'
  }},
  name: '{}',
}};

""".format(tracename, ",".join(xs), ",".join(ys), line, C.country))
        idx += 1

    logaxis = """  yaxis: {
    type: 'log',
    autorange: true
  },
"""

    sys.stdout.write("""
var data = [{}];

var layout = {{
  title: 'Selected countries',
  xaxis: {{
    tickangle: -90
  }},
  {}
  barmode: 'group',
}};

Plotly.newPlot('{}', data, layout);
}}
""".format(", ".join(traces), logaxis if uselog else "", divname))
