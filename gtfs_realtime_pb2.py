# gtfs_realtime_pb2.py — écrit à la main, compatible protobuf 3.x/4.x/5.x/6.x
# Subset minimal GTFS-RT : FeedMessage > entity > trip_update > stop_time_update

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

_sym_db = _symbol_database.Default()

# Sérialisation du FileDescriptorProto en base64 (généré manuellement)
# Pour éviter toute dépendance à grpc_tools ou runtime_version,
# on utilise l'API descriptor_pool.Add() avec un proto sérialisé.
# Ici on utilise une approche encore plus simple : descriptor inline.

from google.protobuf import descriptor_pb2 as _descriptor_pb2

_PROTO = """
syntax = "proto2";
package transit_realtime;
message FeedMessage {
  required FeedHeader header = 1;
  repeated FeedEntity entity = 2;
}
message FeedHeader {
  required string gtfs_realtime_version = 1;
  optional uint64 timestamp = 2;
}
message FeedEntity {
  required string id = 1;
  optional TripUpdate trip_update = 3;
}
message TripUpdate {
  required TripDescriptor trip = 1;
  repeated StopTimeUpdate stop_time_update = 2;
}
message TripDescriptor {
  optional string trip_id = 1;
  optional string route_id = 5;
  optional string trip_headsign = 6;
}
message StopTimeUpdate {
  optional uint32 stop_sequence = 1;
  optional string stop_id = 4;
  optional StopTimeEvent arrival = 2;
  optional StopTimeEvent departure = 3;
}
message StopTimeEvent {
  optional int32 delay = 1;
  optional int64 time = 2;
}
"""

# Charger via l'API publique stable
import subprocess, sys, os, tempfile

def _build_classes():
    """Construit les classes Message en parsant le .proto via protoc en mémoire."""
    try:
        # Tentative 1 : utiliser descriptor_pool avec sérialisation binaire
        # On encode le proto en FileDescriptorProto programmatique
        pool = _descriptor_pool.DescriptorPool()
        
        fdp = _descriptor_pb2.FileDescriptorProto()
        fdp.name = "gtfs-realtime.proto"
        fdp.package = "transit_realtime"
        fdp.syntax = "proto2"
        
        def add_msg(name, fields):
            md = fdp.message_type.add()
            md.name = name
            for fn, ft, fn_num, label, type_name in fields:
                f = md.field.add()
                f.name = fn
                f.number = fn_num
                f.label = label  # 1=optional,2=required,3=repeated
                f.type = ft      # 9=string,4=uint64,11=message,5=int32,3=int64,13=uint32
                if type_name:
                    f.type_name = type_name
            return md

        LABEL_REQUIRED = 2
        LABEL_OPTIONAL = 1
        LABEL_REPEATED = 3
        TYPE_STRING  = 9
        TYPE_UINT64  = 4
        TYPE_UINT32  = 13
        TYPE_INT32   = 5
        TYPE_INT64   = 3
        TYPE_MESSAGE = 11

        add_msg("FeedHeader", [
            ("gtfs_realtime_version", TYPE_STRING, 1, LABEL_REQUIRED, ""),
            ("timestamp", TYPE_UINT64, 2, LABEL_OPTIONAL, ""),
        ])
        add_msg("StopTimeEvent", [
            ("delay", TYPE_INT32, 1, LABEL_OPTIONAL, ""),
            ("time",  TYPE_INT64, 2, LABEL_OPTIONAL, ""),
        ])
        add_msg("TripDescriptor", [
            ("trip_id",       TYPE_STRING, 1, LABEL_OPTIONAL, ""),
            ("route_id",      TYPE_STRING, 5, LABEL_OPTIONAL, ""),
            ("trip_headsign", TYPE_STRING, 6, LABEL_OPTIONAL, ""),
        ])
        add_msg("StopTimeUpdate", [
            ("stop_sequence", TYPE_UINT32,  1, LABEL_OPTIONAL, ""),
            ("arrival",       TYPE_MESSAGE, 2, LABEL_OPTIONAL, ".transit_realtime.StopTimeEvent"),
            ("departure",     TYPE_MESSAGE, 3, LABEL_OPTIONAL, ".transit_realtime.StopTimeEvent"),
            ("stop_id",       TYPE_STRING,  4, LABEL_OPTIONAL, ""),
        ])
        add_msg("TripUpdate", [
            ("trip",              TYPE_MESSAGE, 1, LABEL_REQUIRED, ".transit_realtime.TripDescriptor"),
            ("stop_time_update",  TYPE_MESSAGE, 2, LABEL_REPEATED, ".transit_realtime.StopTimeUpdate"),
        ])
        add_msg("FeedEntity", [
            ("id",          TYPE_STRING,  1, LABEL_REQUIRED, ""),
            ("trip_update", TYPE_MESSAGE, 3, LABEL_OPTIONAL, ".transit_realtime.TripUpdate"),
        ])
        add_msg("FeedMessage", [
            ("header", TYPE_MESSAGE, 1, LABEL_REQUIRED, ".transit_realtime.FeedHeader"),
            ("entity", TYPE_MESSAGE, 2, LABEL_REPEATED, ".transit_realtime.FeedEntity"),
        ])

        pool.Add(fdp)

        # Construire les classes via message_factory
        from google.protobuf import message_factory as _mf
        # Essayer les différentes APIs selon la version de protobuf installée
        classes = None
        # API protobuf 5.x+ (recommandée)
        if hasattr(_mf, 'GetMessageClassesForFiles'):
            classes = _mf.GetMessageClassesForFiles([fdp.name], pool)
        # API protobuf 4.x
        elif hasattr(_mf, 'GetMessages'):
            classes = _mf.GetMessages([fdp])
        # API protobuf 3.x / legacy
        else:
            factory = _mf.MessageFactory(pool=pool)
            classes = factory.GetMessages([fdp])
        if classes is None:
            classes = {}

        return classes, pool, fdp

    except Exception as e:
        raise RuntimeError(f"Impossible de construire les descripteurs GTFS-RT: {e}")

_classes, _pool, _fdp = _build_classes()

def _get(name):
    return _classes.get(f"transit_realtime.{name}")

FeedMessage     = _get("FeedMessage")
FeedHeader      = _get("FeedHeader")
FeedEntity      = _get("FeedEntity")
TripUpdate      = _get("TripUpdate")
TripDescriptor  = _get("TripDescriptor")
StopTimeUpdate  = _get("StopTimeUpdate")
StopTimeEvent   = _get("StopTimeEvent")

if FeedMessage is None:
    raise ImportError("Échec construction FeedMessage — vérifiez la version de protobuf")
